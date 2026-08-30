from pydantic import BaseModel


class ExtractedField(BaseModel):
    value: str | int | float | bool
    source_url: str
    snippet: str
    # ISO8601 per-field TTL (spec FR4). Empty means "no explicit TTL" and is
    # treated as stale by the cache freshness check, which is the safe default.
    ttl_expires_at: str = ""


class ProductEntity(BaseModel):
    entity_id: str
    fields: dict[str, ExtractedField]
    extracted_at: str  # ISO8601
    ttl_expires_at: str  # ISO8601

    def get_price(self) -> float | None:
        price_field = self.fields.get("price")
        if price_field is None:
            return None
        return float(price_field.value)

    def get_name(self) -> str:
        name_field = self.fields.get("name")
        if name_field and str(name_field.value).strip() and str(name_field.value).strip().lower() != "unknown product":
            return str(name_field.value).strip()
        # Fallback: extract title from snippet or source_url
        for f in self.fields.values():
            if f.snippet:
                first_line = f.snippet.split("\n")[0].strip()
                if len(first_line) > 5 and not first_line.startswith("http"):
                    return first_line[:80]
            if f.source_url:
                import urllib.parse
                path = urllib.parse.urlparse(f.source_url).path.strip("/").split("/")[-1]
                clean = path.replace("-", " ").replace("_", " ").title()
                if len(clean) > 3:
                    return clean[:80]
        return "Featured Product"

