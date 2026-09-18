# Orda: Your Work Runs in the Background

Orda keeps track of your ongoing work. You just send notes. Orda files each one in the right place.

Think of a helper behind the counter. You speak. It sorts. You keep working.

## What Orda is

Orda is a Quiet sorter for your daily notes.

You send it short notes through the day. It files each note under the right project. It keeps one notebook per project.

You never sort threads by hand. You never copy old notes forward. Orda does that part.

## What you do

You do one thing: send notes.

Type plain words. Short is fine. Long is fine. One topic or two.

> Milk low. Bread low. Order by Thursday.
> Draft a kind reply to the rude review from Tuesday.
> Remind me at 6 pm to lock the back door.

That is all. Orda reads each note and files it.

## How Orda files your notes

It keeps one notebook per project. Each notebook has a short label, like `store` or `home-fix` or `school-trip`.

A new note lands in one of two ways:

- It continues a notebook you already have. Same topic, same notebook.
- It starts a new notebook. New topic, new notebook.

Orda picks by reading the words and the short labels. If your note names a label straight out, that wins. If not, Orda compares words in your note with the short summary on each notebook.

If Orda is not sure, it asks you. It never guesses on your behalf. It parks the note and shows you the two closest labels. You pick.

## How Orda recalls without keeping everything

Orda keeps short notes, not full copies.

Each notebook holds a brief summary. Five hundred letters at most. Not the whole past. Just the gist: what the project is, what is still open, what comes next.

When one notebook needs a fact from another, Orda passes a short slip. Two thousand letters at most. Newest facts first. Old facts drop off first. The slip says when bits were cut.

So old notes stay where they were. Orda carries the gist forward, not the pile.

## Fix it when it files wrong

Orda files wrong at times. Fix it with one line:

```
orda correct <note-id> --to <label>
```

Find your note's ID and the right label first:

```
orda topics
orda show <label>
```

`orda topics` lists each label with a one-line summary. `orda show <label>` shows that notebook's state and recent picks.

Your fix is kept on record. The note moves. The wrong file is marked.

Two notebooks on the same thing? Join them:

```
orda merge <label-a> <label-b> --into <label>
```

One notebook that should be two? Cut it at a note:

```
orda split <label> --at <note-id> --new <label>
```

Need quiet for a while? Hold new notes for one label, then let them flow again:

```
orda pause <label>
orda resume <label>
```

## Examples from real days

### Home

> The tap in the back bath still drips. Call the plumber Friday.
> Add soup, rice, and soap to the shop list.

First note goes to the `home-fix` notebook. Next note starts or joins the shop list. Two notes, two right places.

### Work

> Move the client call to 3 pm. Send them the new dates.
> The deck for Monday is done. Check my spelling.

Orda files the call note with the client thread. It files the deck note with the Monday work. You check the draft before it goes out. See the safety part below.

### Business

> Send quotes to the two new leads by noon.
> Pay the power bill before the late fee hits.

Quotes go to sales. The bill goes to bills. Anything that spends or sends waits for your yes first.

### Chores

> Remind me to take the bins out Tuesday night.
> The porch light is out. Buy a bulb.

Bins go to the home-chore thread. The bulb joins the shop list or the fix list. Small notes, filed away.

### Research

> Find three reviews of quiet fans. Under $100. Low power use.
> How does the school grant form work? List the steps.

Reviews go to the fan research thread. The grant form starts a new thread or joins school work. Old findings stay in their notebooks. New notes add to them.

### Convenience store: a full day

You run a corner store. Here is Orda through your day.

**Stock reminders.** Morning. You type:

> Milk low, eggs low, bread low. Order by Thursday.

Orda files this in your `store-stock` notebook. It adds to the same list as yesterday. One list, always current.

**Supplier comparisons.** Midday. A new rep drops a price sheet. You type:

> New rep from FreshLine. Milk 10 cents cheaper. Eggs 5 cents dearer. Worth a switch?

This is a new question. Orda starts a `store-supplier` thread or adds to past supplier notes. Old price notes stay on file. The new sheet sits next to them. You see both, side by side.

**Customer-note drafts.** Afternoon. A bad review stings. You type:

> Draft a kind reply to the review about the long queue on Tuesday. Say sorry. Say what we will fix.

Orda drafts the reply in your `store-notes` thread. The draft waits. You read it. You say yes. Only then does it go out. Nothing rude goes out in heat.

**Staff plans.** Evening. Cover for Saturday is thin. You type:

> Ali wants Saturday off. Mina can cover till 2. Who covers after 2?

Orda files this in your `store-staff` thread. Past rota notes stay there. The gap stands out. You fill it.

**Daily tasks.** Close. Same jobs each night. You type:

> Close list: bins out, shutters half, fridge temps, cash count.

Orda keeps this as a daily round in your `store-close` thread. Each night adds a tick. Miss a step and the list shows it.

Five jobs. Five notebooks. One stream of notes from you.

## Safety: your yes comes first

Some acts cannot be undone. Orda knows the list: sending, posting, spending, erasing, changing shared work.

For these, Orda always stops and asks. No is the default. Nothing moves till you say yes in plain words.

See what waits for your yes:

```
orda approvals
```

Each item shows what it wants to do and why. You allow it or you deny it. No quiet sends. No quiet spends.

## Privacy: private bits are stripped first

Keys, tokens, and secret codes are scrubbed before any helper sees your note. Orda swaps each one for a tag like `[REDACTED:key]`. It counts what it scrubbed.

Strict shops can set a hard rule: if a note holds a secret, Orda will not pass it on at all. It holds the note and tells you.

Orda's own logs keep counts and picks only. Never your words. Never your secrets.

## What Orda will not do

- It will not send, post, spend, erase, or change shared work without your yes.
- It will not guess when two notebooks fit. It will ask.
- It will not drag your whole past along. Short notes only.
- It will not start secret local services on your machine. If you want a helper that runs on your own box, you set that up and name it in the config. Orda never starts it for you.

## Quick start for the non-technical reader

1. Open Orda where you normally type notes.
2. Send a note in plain words.
3. If Orda asks which notebook, pick one.
4. If Orda files wrong, run the one-line fix above.
5. If Orda waits for a yes, check `orda approvals`.

That is the whole job. You send notes. Orda keeps the notebooks.
