# Orda: A Plain-Language Guide

Orda is one input for getting work done with AI. You type what you want in plain words. You press send. One result comes back. One box for input. The backend does the work.

## What is in this repository

This repository holds the interface and a stand-in backend. The stand-in records your request and returns an acknowledgement with a session id. It writes no text. Live production uses a real backend.

## How to use it

1. Open Orda.
2. Type what you want in your own words.
3. Press send and read what comes back.

You do not set anything up. You describe the job. A short request is fine. A long request is fine. A request can have more than one part.

## Four things you can ask for

Each case shows the request shape only.

### A messy document, made into a clean summary

A supplier sends a long update. Only some parts matter. You type:

> Here is my supplier's update. Give me a short summary I can read in a minute.

Then you paste it.

Shape only, no text. The shipped backend records the request and returns an acknowledgement. Result wording only shows where a live result would appear.

### A reply to a difficult message

A customer is angry about a late delivery. You type:

> A customer is upset that their order arrived late. Write a short reply that offers a refund and a small discount.

Shape only, no text. The shipped backend records the request and returns an acknowledgement. Result wording only shows where a live result would appear.

### Decisions and dates from a long chain

You have many messages about one project and lost track of what was agreed. You type:

> Here is a long email chain about the shop move. List every decision we made and every date we agreed.

Shape only, no text. The shipped backend records the request and returns an acknowledgement. Result wording only shows where a live result would appear.

### A rough piece of writing, reworked

You wrote something in a hurry. You type:

> Rewrite this so it is clear and friendly, and keep it short.

Then you paste it.

Shape only, no text. The shipped backend records the request and returns an acknowledgement. Result wording only shows where a live result would appear.

## What Orda asks you first

Orda stops and waits before it would send, post, spend, delete, or change shared work. The answer starts as no. Orda shows what it will do and waits. Nothing goes out until you say yes.

## When Orda is off or busy

- If Orda is off, send your request when it is back.
- If many requests arrive at once, they wait in line. Nothing you sent is lost.
- You can keep typing while Orda catches up. It takes requests in order.

## If something goes wrong

| What you see | What to do |
|---|---|
| You never see a result | Send the request again. Asking twice is harmless. |
| The result is not what you wanted | Say what to change in one line. Try Shorter. Warmer. Only the dates. |
| Orda asks a question first | Answer it. It is checking what you meant. |
| Nothing seems to happen | Orda may be waiting for your yes. Look at what it holds, then allow or refuse. |
| The result stops partway | Ask for the rest. What you have is kept. |

## What Orda will not do

- It will not send, post, spend, or delete without your yes.
- It will not change shared work on its own.
- It will not guess when a request could mean two things. It asks.
- It will not start work until you send the request.
- It will not keep passwords or card numbers. They are removed before any work begins.
