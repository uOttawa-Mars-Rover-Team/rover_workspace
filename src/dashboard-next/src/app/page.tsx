import Card from "./components/Card"

export default function Home() {
  return (
    <main className="flex-1 p-3">
      <Card title="Test Card">
        <p className="text-muted">This is a test card.</p>
      </Card>
    </main>
  )
}