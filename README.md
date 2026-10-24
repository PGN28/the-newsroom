# The Newsroom

A lightweight personal news dashboard for India, Kerala, world affairs, CLAT GK, law and politics.

## Sections and display

- **India, Kerala, World Affairs, Law, Politics, CLAT GK** are shown in one tabbed interface.
- Each section displays up to 12 stories in a responsive three-column grid.
- Stories link to their original publishers. The site does not store full article text or publisher images.
- Politics uses party/event labels: BJP, INC, CPI(M), CJP, IUML, AAP and CPI. Labels are based on headline matching and are only a rough classifier, not an assessment of a party's overall record or the truth of an allegation.
- CLAT GK marks stories with **WHAT HAPPENED**. The GDELT DOC API supplies article metadata and headlines, not dependable explanatory summaries. When no description is available, the interface explicitly says that more context must be read at the publisher. Do not treat a headline alone as a complete current-affairs note.

## Data refresh

The GitHub Actions workflow in `.github/workflows/update-news.yml` refreshes the JSON index every four hours and can also be started manually from **Actions → Update news index → Run workflow**.

The collector searches the GDELT DOC API for English-language coverage from the preceding 72 hours, ranks results with simple relevance/recency rules, and writes at most 12 stories per section to `data/news.json`. Search coverage, relevance and publisher metadata are imperfect; this is a discovery tool, not a comprehensive news archive.

## Deploying the website

The site is static HTML/CSS/JavaScript. A straightforward option is Cloudflare Pages connected to this GitHub repository:

1. Open the Cloudflare dashboard and go to **Workers & Pages**.
2. Choose **Create application → Pages → Connect to Git**.
3. Authorize GitHub and select `PGN28/the-newsroom` (the repository can remain private).
4. Use `main` as the production branch. Leave the build command empty and set the build output directory to `.` (the repository root).
5. Deploy. Cloudflare will provide a `pages.dev` address and deploy later pushes automatically.

The public site itself is accessible to visitors even when the source repository is private. Keep credentials and private information out of the repository.

## Rights and limitations

This project links to publisher reports and displays headlines/metadata returned by GDELT. A link does not grant permission to republish a publisher's headline, description, article text or images. Rights and reuse terms vary by publisher and applicable law; this README is not legal advice. Review publisher terms and remove material if a rights holder raises a concern.

GDELT is used as an article-discovery source; it does not verify every claim or guarantee balanced coverage. Political labels are mechanical and can be wrong. Always open the linked source for context and corrections.
