from fastapi import APIRouter, Depends, HTTPException

from ..adapters.github_api import GitHubAPIAdapter
from ..agent import run_review_agent
from ..config import get_settings
from ..errors import BuilderGuardError
from ..github_url import parse_pr_url
from ..groq_client import GroqClient
from ..schemas import ReviewRequest, ReviewResponse
from ..security.rate_limit import RateLimiter
from ..session import ReviewSession

router = APIRouter()

# Each review drives several real Groq API calls, so this endpoint gets the
# same abuse protection as the Security Lab's run endpoint.
_review_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)


@router.post(
    "/api/reviews",
    response_model=ReviewResponse,
    dependencies=[Depends(_review_rate_limiter)],
)
async def create_review(payload: ReviewRequest) -> ReviewResponse:
    settings = get_settings()

    try:
        owner, repo, pull_number = parse_pr_url(payload.pr_url)
    except BuilderGuardError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    session = ReviewSession(pr_url=payload.pr_url)
    adapter = GitHubAPIAdapter(settings)
    groq_client = GroqClient(settings)

    try:
        return await run_review_agent(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            adapter=adapter,
            groq_client=groq_client,
            settings=settings,
            session=session,
        )
    except BuilderGuardError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - last-resort safety net
        raise HTTPException(
            status_code=500, detail="Internal error while generating the review"
        ) from exc
