// Cloudflare Worker — proxies workflow dispatch to GitHub API.
// Deploy via Cloudflare dashboard, then add a secret named GITHUB_TOKEN
// (fine-grained PAT with Actions: write on Fair-Forward/datasets only).

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return cors(new Response(null, { status: 204 }));
    }

    if (request.method !== "POST") {
      return cors(new Response("Method not allowed", { status: 405 }));
    }

    const res = await fetch(
      "https://api.github.com/repos/Fair-Forward/datasets/actions/workflows/update_from_google_sheets.yml/dispatches",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_TOKEN}`,
          Accept: "application/vnd.github+json",
          "Content-Type": "application/json",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "fair-forward-trigger-worker",
        },
        body: JSON.stringify({ ref: "main" }),
      }
    );

    if (res.status === 204) {
      return cors(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    }

    const body = await res.json().catch(() => ({}));
    return cors(
      new Response(
        JSON.stringify({ ok: false, message: body.message || `HTTP ${res.status}` }),
        { status: res.status }
      )
    );
  },
};

function cors(response) {
  const headers = new Headers(response.headers);
  headers.set("Access-Control-Allow-Origin", "*");
  headers.set("Access-Control-Allow-Methods", "POST, OPTIONS");
  headers.set("Content-Type", "application/json");
  return new Response(response.body, { status: response.status, headers });
}
