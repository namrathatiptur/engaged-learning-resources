# TeachOrange — To-Do

Task list in priority order (from your requirements).

**Status:** ✅ done · 🟡 done with placeholders (needs your content) · ⬜ not started

---

## 1. Categories — ✅ done (flat list)
- [x] Added all 10 categories via migration `0006_add_curriculum_categories` (deploys automatically):
      Group Activity · Individual Activity · Whole Class Activity · Creative Visual Activity ·
      Creative Performance Activity · Class Presentation Component · Outside of Classroom Activity ·
      Civic Engagement · Policy · Business and Economics
- [ ] **Open decision:** currently an activity picks ONE category. If you want an activity to be both a
      *type* (Group/Individual…) and a *subject* (Policy/Civic…), we split into two dimensions later.

## 2. Meet the Team page — 🟡 built with placeholders
- [x] New page at `/team/` (linked in the footer)
- [x] 3 member cards (Me / You / Ben) with initials avatars, roles, bios — all placeholder
- [x] Headshot support ready (drop images in `static/team/` or upload)
- [ ] **Needs from you:** real names, photos, bios (email)

## 3. Contact form that routes to your email — ✅ done
- [x] Contact page is now a **2-column split**: team on the left, message form on the right
- [x] Form (name, email, subject, message) emails **mdbrockw@syr.edu** (Reply-To = sender) — verified working
- [x] Honeypot spam guard + success/error flash messages
- [ ] **For production sending:** set SMTP env vars (`DJANGO_EMAIL_HOST`, `..._USER`, `..._PASSWORD`).
      Change destination with `DJANGO_CONTACT_EMAIL` if not mdbrockw@syr.edu.

## 4. "TeachOrange Consulting" page — 🟡 built with placeholders
- [x] New page at `/consulting/` (linked in nav + footer): navy hero + 3 service cards + CTA
- [ ] **Needs from you:** real overview, services, and details (email)

## 5. Thumbnail → click to pop out — ✅ done (popout); rasterized thumbnail is a follow-up
- [x] Clicking a card image opens a **lightbox popout** with the activity's title, category, and description
- [x] Signed-in users see the actual **material preview embedded** (PDF/image) inside the popout
- [x] Signed-out users get a "sign in with your .edu to preview" prompt
- [ ] **Follow-up:** to make the *thumbnail itself* literally the document's first page, we need a
      PDF→image render step (extra library). The popout already delivers "click to get an idea."

---

## Needs a decision / content from you
- Category model: keep flat, or split into type + subject (item 1)
- Team names / photos / bios (item 2) — email
- Consulting copy (item 4) — email
- Confirm contact-form destination address (item 3, defaulted to mdbrockw@syr.edu)
- Production email (SMTP) credentials for real sending

## Shipping
- [ ] Commit everything to a branch (as `namrathatm`) and open a PR
- [ ] Deploy (includes the Contact 500 fix + all of the above)
