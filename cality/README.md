# Cality landing page

Static landing page, added September 25, 2026. No install or build step.

Preview from the repository root with `python3 -m http.server 8765`, then open `/cality/`.

## Assets

Fresh Simulator screenshots from the installed September 25 QA app, English locale, fictional ScreenshotWorkspace items. Weather location is Los Angeles. No private EventKit events or reminders were used. No full weather screenshot is included because this installed QA version still shows a sample forecast. Original captures are unmodified PNGs; app icon comes from Cality's own asset catalog.

## Publishing

The current GitHub Pages repository hosts wystoneapps.com. The Cality route is /cality/. Do not replace its root CNAME.

For cality.wystoneapps.com, create a separate GitHub Pages repository containing this directory at its root, with CNAME set to cality.wystoneapps.com. Configure a Namecheap CNAME for host cality pointing to wystoneapps.github.io, enable HTTPS in the new repository, then change canonical, og:url and SoftwareApplication URL to https://cality.wystoneapps.com/ and point the Wystone card to it. Keep /cality/ as a redirect or set its canonical to the subdomain. Do not point the subdomain at the existing homepage repository and expect path routing.

No analytics, signup form, cookies or paid services added. US pricing is explicitly labelled. No fabricated ratings or review schema.
