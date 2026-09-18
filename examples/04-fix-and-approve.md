# Example 4 — Wrong thread fix plus a send that waits for a yes

Notebooks: `store-notes` ("Draft replies to customer reviews."), `home-chores`.

Transcript:

> **Owner:** Draft a kind reply to the review about the long queue on Tuesday.
> **Orda:** Filed under `home-chores`. Draft ready.
> **Owner:** Wrong place. That belongs with the store notes.
> **Owner runs:** `courier correct <note-id> --to store-notes`
> **Orda:** Moved. The wrong file is marked. The draft now sits under `store-notes`.
> **Orda:** Draft reply is ready. It will NOT go out till you say yes. See `courier approvals`.
> **Pick:** CONTINUE after fix (`store-notes`), plus APPROVAL_REQUIRED on the send — sends wait for an explicit yes.

Rules shown: one-line fix moves a misfiled note and leaves a record. Anything that sends or posts always waits for a yes. No is the default.
