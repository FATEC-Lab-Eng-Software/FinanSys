import { notFound } from "next/navigation";
import { routes } from "../../generated/routes";

export default async function GeneratedRoute({ params }: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await params;
  const routePath = `/${slug.join("/")}`;
  const Page = routes[routePath as keyof typeof routes];

  if (!Page) notFound();
  return <Page />;
}
