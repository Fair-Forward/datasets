// The fair-sharing guidance, shown in the header's "Fair sharing" modal and as the
// "Kind Reminder" at the end of every project's detail panel. One component so the two
// copies cannot drift.
//
// Condensed from the FAIR Forward Impact Report and Replication Kit, "Recommendations to
// (big) tech and other institutions planning to use open-source AI, which has been developed
// by a community or under-resourced governments" (p. 83). Keep it faithful to the report;
// the full text is behind the link. PDF page indices match the printed page numbers.
export const FAIR_SHARING_REPORT_URL =
  'https://www.bmz-digital.global/wp-content/uploads/2026/08/FAIR-Forward-Impact-Report-and-Replication-Kit-AI-by-and-for-all-GIZ-2026-10MB.pdf#page=83'

const FairSharingRecommendations = () => (
  <div className="fair-sharing">
    <p className="fair-sharing-intro">
      If you use open-source AI data, models or other resources that local communities or under-resourced
      governments collected, aggregated, curated and vetted, contribute to a fair sharing of any (monetary or
      general) value. Concretely, this means:
    </p>
    <ol className="fair-sharing-list">
      <li>
        Acknowledge and attribute any use of such data. Almost all open-source licenses require this; do it in
        all cases.
      </li>
      <li>
        Share any improved version back with the community or government, so all parties build a better AI
        together. “Share-alike” licenses require this; it is strongly encouraged in all cases.
      </li>
      <li>
        Contact the communities and work out together how value can be shared more fairly. Needs might include
        access to compute, so communities can fine-tune models for local contexts, or capacity building.
      </li>
      <li>
        Discuss a pathway for communities and under-resourced governments to access the same resources
        (compute, skills), and frameworks for capacity building or other needs, to create a level playing field
        and allies for joint work on an AI commons.
      </li>
    </ol>
    <a
      href={FAIR_SHARING_REPORT_URL}
      target="_blank"
      rel="noopener noreferrer"
      className="fair-sharing-link"
    >
      Long version: FAIR Forward Impact Report, pages 83–85 (PDF, 32 MB)
    </a>
  </div>
)

export default FairSharingRecommendations
