# Router Agent

## Purpose

The Router Agent classifies a student's university FAQ question
into one of four supported domains.

## Supported Routes

- fees_academics
- placements
- campus_hostel
- unknown

## Main Function

```python
from agents.router import route

domain = route(question)