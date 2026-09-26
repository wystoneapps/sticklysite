# MarkSave dedicated website

Live: https://wystoneapps.com/marksave/

Static HTML and CSS, served by the existing Wystone GitHub Pages repository. No scripts, trackers, forms, paid dependencies or new hosting services.

## September 26 showcase update

- Hero covers video, space, technology and travel instead of recipes alone.
- Current native Reader capture replaces the older App Store composite.
- Lists and My Board have a dedicated, explicitly upcoming preview section. Verified public version is 2.4.0; do not describe these as released until App Store availability is checked.
- iPhone, iPad and Mac store destinations retained. Root homepage code is untouched; its shared library image now receives the broader demo too.

## Screenshot provenance

Four actual native MarkSave view captures from the signed-out **MarkSave Reader QA** simulator, UUID D515C20A-AAC2-4D8A-91EE-D92D33BBEC25. Produced by `ReaderLayoutTests.testMarketingShowcaseLayouts` on the personal-board-pins branch. No user's saves were used. The fixture refuses to run in a nonempty library, deletes only its own fixture IDs, and uses an in-memory store for Lists and My Board. Example titles and the Reader article were written for this demo, not attributed to a real publisher.

Source photographs for illustrative content (Unsplash):
- Kyoto: https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e
- Technology: https://images.unsplash.com/photo-1518770660439-4636190af475
- Earth: https://images.unsplash.com/photo-1446776811953-b23d57bd21aa

Screens are not AI-generated mockups. Lists and Board crops hide only unused space below the native interface. The Simulator capture has no operating-system status bar.

## Publish

Commit only this directory and push the existing main branch. GitHub Pages publishes automatically. Verify the live route, all four screenshots, mobile overflow and App Store destinations. Keep the root homepage owned by the studio/Cality task.
