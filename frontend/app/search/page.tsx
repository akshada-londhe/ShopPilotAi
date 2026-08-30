import { Suspense } from "react";
import { SearchResultPage } from "../../components/search/SearchResultPage";

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const params = await searchParams;
  return (
    <Suspense fallback={<div className="sp-container py-20 text-center text-[#7050f0]">Loading search...</div>}>
      <SearchResultPage initialQuery={params?.q ?? ""} />
    </Suspense>
  );
}