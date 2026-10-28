type CardProps = {
    title: string;
    children: React.ReactNode;
}

export default function Card({
    title,
    children
}: CardProps) {
    return (
        <section className="bg-panel border border-line rounded-xl p-3">
            <h2 className="mb-2 text-lg font-semibold">{title}</h2>
            {children}
        </section>
    )
}