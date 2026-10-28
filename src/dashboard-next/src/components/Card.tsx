type CardProps = {
    title: string;
    children?: React.ReactNode;
    className?: string;

}

export default function Card({
    title,
    children, 
    className
}: CardProps) {
    return (
        <section className={`bg-panel border border-line rounded-xl p-3 ${className ?? ""}`}>
            <h2 className="mb-2 text-lg font-semibold">{title}</h2>
            {children}
        </section>
    )
}