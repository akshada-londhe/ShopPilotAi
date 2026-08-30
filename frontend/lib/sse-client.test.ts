import { describe, expect, it, vi, beforeEach } from "vitest";
import { streamSearch } from "./sse-client";

function makeStreamResponse(chunks: string[]): Response {
    const encoder = new TextEncoder();
    let index = 0;
    const stream = new ReadableStream({
    pull(controller) {
        if (index < chunks.length) {
        controller.enqueue(encoder.encode(chunks[index]));
        index++;
        } else {
        controller.close();
        }
    },
    });
    return new Response(stream, { status: 200 });
}

describe("streamSearch", () => {
    beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    });

    it("parses a sequence of SSE events from the stream", async () => {
    const sseText =
        'data: {"event": "progress", "payload": {"stage": "normalizing", "message": "..."}}\n\n' +
        'data: {"event": "result", "payload": {"products": [], "synthesis": "Done!", "metadata": {"iterations": 1, "is_best_available": false, "weighted_score": 8.0, "assumptions_made": []}}}\n\n';

    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(makeStreamResponse([sseText]));

    const events = [];
    for await (const evt of streamSearch("gaming mouse under 2000")) {
        events.push(evt);
    }

    expect(events).toHaveLength(2);
    expect(events[0].event).toBe("progress");
    expect(events[1].event).toBe("result");
    if (events[1].event === "result") {
        expect(events[1].payload.synthesis).toBe("Done!");
    }
    });

    it("sends the query and clarification context in the request body", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(makeStreamResponse([""]));

    const gen = streamSearch("phone", { round: 1, previous_questions: ["budget?"], user_answers: ["10000"] });
    for await (const evt of gen) {
      void evt;
    }

    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    const body = JSON.parse(options.body);
    expect(body.query).toBe("phone");
    expect(body.clarification_context.round).toBe(1);
    });

    it("posts to /api/search with Content-Type header", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(makeStreamResponse([""]));

    const gen = streamSearch("mouse");
    for await (const evt of gen) {
      void evt;
    }

    const [url, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toBe("/api/search");
    expect(options.headers["Content-Type"]).toBe("application/json");
    });
});