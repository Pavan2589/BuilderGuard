function formatCategory(category) {
  return category
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export default function CategorySelector({ categories, selected, onSelect }) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onSelect('all')}
        className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
          selected === 'all'
            ? 'bg-neutral-900 text-white'
            : 'bg-white text-neutral-600 ring-1 ring-inset ring-neutral-200 hover:bg-neutral-50'
        }`}
      >
        All categories
      </button>
      {categories.map((category) => (
        <button
          key={category}
          onClick={() => onSelect(category)}
          className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
            selected === category
              ? 'bg-neutral-900 text-white'
              : 'bg-white text-neutral-600 ring-1 ring-inset ring-neutral-200 hover:bg-neutral-50'
          }`}
        >
          {formatCategory(category)}
        </button>
      ))}
    </div>
  )
}

export { formatCategory }
