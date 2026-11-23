import { BookOpen, ExternalLink } from "lucide-react";

import type { AssistantBook } from "../../types/assistant";

type BookRecommendationsProps = {
    books: AssistantBook[];
};

function BookRecommendations({ books }: BookRecommendationsProps) {
    if (books.length === 0) return null;

    return (
        <ul className="mt-3 space-y-3" aria-label="Livros recomendados pelo Google Books">
            {books.map((book) => (
                <li key={book.info_link}>
                    <article className="rounded-xl border border-slate-200 bg-white p-3 text-slate-800 shadow-sm">
                        <a
                            href={book.info_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-start gap-2 font-semibold text-secondary hover:underline"
                        >
                            <BookOpen size={17} className="mt-1 shrink-0" aria-hidden="true" />
                            <span>{book.title}</span>
                        </a>
                        {book.authors.length > 0 && <p className="mt-1 text-xs text-slate-600">{book.authors.join(", ")}</p>}
                        {book.published_date && <p className="mt-1 text-xs text-slate-500">Publicado em {book.published_date}</p>}
                        {book.description && <p className="mt-2 text-xs leading-5 text-slate-600">{book.description}</p>}
                        <a
                            href={book.info_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-secondary hover:underline"
                        >
                            Ver no Google Books <ExternalLink size={13} aria-hidden="true" />
                        </a>
                    </article>
                </li>
            ))}
        </ul>
    );
}

export default BookRecommendations;
