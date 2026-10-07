# Image prompts for the mood pictures

Prompts for Gemini to make the teacher's mood pictures (NOTES #38, PLAN.md
11.5). The game shows `<picture>_<mood>` instead of `<picture>` on that
mood's day when the file exists in `assets/images/`; nothing else needs to
change. A missing picture falls back to the normal one, so any subset works.

## How to use

1. For each picture: upload the image(s) listed under **Upload** from
   `assets/images/` (in that order), paste the prompt as it is, and save the
   result in `assets/images/` under the name in **Save as** (`.jpeg`,
   `.jpg` or `.png` all work; the name before it must match exactly).
2. **Order matters:** make **B1, D1 and N1 first**. The others upload them as
   a second, reference image so the hat, cake, suit or phone look the same in
   every picture. Remake B1 / D1 / N1 until you like them.
3. **Check every result** against its source: the teacher's head, the
   students, the desks and the paper must not move. The warning scene zooms
   in on fixed spots of his face, and the neighbours' papers are looked for
   at fixed spots. If something moved, generate it again.
4. The top of every picture is cut off in the game: decorations belong on
   the walls, the board and the desks, not only on the ceiling.
5. To see a mood in the game, temporarily set the Quiz's `"moods"` in
   `QUIZZES` (settings.py) to only that mood, e.g. `("birthday",)`, and
   change it back afterwards.

Priority: B1-B4, D1-D4, N1-N2 (seen all exam long), then the scenes
(B6, B7, D5, D6), then B5 and the optional side views (B8).


## Birthday (`birthday`)

### B1

- **Upload:** `classroom_board_busy.jpeg`
- **Save as:** `classroom_board_busy_birthday.jpeg`

```
Edit the attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs, doors, the chalkboard or the exam paper and hands in the foreground. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

BIRTHDAY SET (draw these exactly the same way in every picture):
- On the teacher's head, on top of his camouflage bandana: a red-and-yellow striped cone party hat with a white pom-pom.
- On the teacher's desk (the desk at the front left, next to the chalkboard): a small round white birthday cake with pink icing and three lit candles, on a plate.
- Three balloons (red, yellow, blue) tied with strings to the right corner of the teacher's desk.
- A paper banner with colourful letters "HAPPY BIRTHDAY" hanging on the wall just above the chalkboard.
- A little colourful confetti on the floor at the front of the classroom.

The teacher is still facing the board, erasing it.
```

### B2

- **Upload:** 1. `classroom_board_watching.jpeg`, 2. `classroom_board_busy_birthday.jpeg`
- **Save as:** `classroom_board_watching_birthday.jpeg`

```
Edit the first attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs, doors, the chalkboard or the exam paper and hands in the foreground. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

The second image is only a reference: draw the birthday hat, cake, balloons, banner and confetti exactly as they look in it. Do not copy anything else from the second image.

BIRTHDAY SET (draw these exactly the same way in every picture):
- On the teacher's head, on top of his camouflage bandana: a red-and-yellow striped cone party hat with a white pom-pom.
- On the teacher's desk (the desk at the front left, next to the chalkboard): a small round white birthday cake with pink icing and three lit candles, on a plate.
- Three balloons (red, yellow, blue) tied with strings to the right corner of the teacher's desk.
- A paper banner with colourful letters "HAPPY BIRTHDAY" hanging on the wall just above the chalkboard.
- A little colourful confetti on the floor at the front of the classroom.

He is facing the class with a slight, proud smile.
```

### B3

- **Upload:** 1. `classroom_desk_busy.jpeg`, 2. `classroom_board_busy_birthday.jpeg`
- **Save as:** `classroom_desk_busy_birthday.jpeg`

```
Edit the first attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs, doors, the chalkboard or the exam paper and hands in the foreground. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

The second image is only a reference: draw the birthday hat, cake, balloons, banner and confetti exactly as they look in it. Do not copy anything else from the second image.

BIRTHDAY SET (draw these exactly the same way in every picture):
- On the teacher's head, on top of his camouflage bandana: a red-and-yellow striped cone party hat with a white pom-pom.
- On the teacher's desk (the desk at the front left, next to the chalkboard): a small round white birthday cake with pink icing and three lit candles, on a plate.
- Three balloons (red, yellow, blue) tied with strings to the right corner of the teacher's desk.
- A paper banner with colourful letters "HAPPY BIRTHDAY" hanging on the wall just above the chalkboard.
- A little colourful confetti on the floor at the front of the classroom.

He sits at his desk next to the cake, smiling at his phone (birthday messages).
```

### B4

- **Upload:** 1. `classroom_desk_watching.jpeg`, 2. `classroom_board_busy_birthday.jpeg`
- **Save as:** `classroom_desk_watching_birthday.jpeg`

```
Edit the first attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs, doors, the chalkboard or the exam paper and hands in the foreground. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

The second image is only a reference: draw the birthday hat, cake, balloons, banner and confetti exactly as they look in it. Do not copy anything else from the second image.

BIRTHDAY SET (draw these exactly the same way in every picture):
- On the teacher's head, on top of his camouflage bandana: a red-and-yellow striped cone party hat with a white pom-pom.
- On the teacher's desk (the desk at the front left, next to the chalkboard): a small round white birthday cake with pink icing and three lit candles, on a plate.
- Three balloons (red, yellow, blue) tied with strings to the right corner of the teacher's desk.
- A paper banner with colourful letters "HAPPY BIRTHDAY" hanging on the wall just above the chalkboard.
- A little colourful confetti on the floor at the front of the classroom.

He sits at his desk next to the cake, looking up at the class, cheerful.
```

### B5

- **Upload:** `classroom_desk_looking_down.jpeg`
- **Save as:** `classroom_desk_looking_down_birthday.jpeg`

```
Edit the attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove the notebook, the hands, the pencil, the breadboard or anything else on the desk. Keep all existing text unchanged. Only make these changes:

It is the teacher's birthday. Add a few pieces of colourful confetti on the wooden desk around the notebook and a rolled-up party blower lying next to the breadboard. Do NOT put anything on the exam paper: the answer lines 1 to 5 must stay completely empty and visible.
```

### B6

- **Upload:** 1. `classroom_warning.jpeg`, 2. `classroom_board_busy_birthday.jpeg`
- **Save as:** `classroom_warning_birthday.jpeg`

```
Edit the first attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs, doors, the chalkboard or the exam paper and hands in the foreground. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

The second image is only a reference: draw the birthday hat, cake, balloons, banner and confetti exactly as they look in it. Do not copy anything else from the second image.

BIRTHDAY SET (draw these exactly the same way in every picture):
- On the teacher's head, on top of his camouflage bandana: a red-and-yellow striped cone party hat with a white pom-pom.
- On the teacher's desk (the desk at the front left, next to the chalkboard): a small round white birthday cake with pink icing and three lit candles, on a plate.
- Three balloons (red, yellow, blue) tied with strings to the right corner of the teacher's desk.
- A paper banner with colourful letters "HAPPY BIRTHDAY" hanging on the wall just above the chalkboard.
- A little colourful confetti on the floor at the front of the classroom.

He is furious: the party hat sits slightly crooked, and he keeps the same angry face and pose, pointing at the viewer. The teacher's desk with the cake is partly visible behind him on the left.
```

### B7

- **Upload:** 1. `classroom_caught.png`, 2. `classroom_board_busy_birthday.jpeg`
- **Save as:** `classroom_caught_birthday.png`

```
Edit the first attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs or doors. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

The second image is only a reference: draw the birthday hat, cake, balloons, banner and confetti exactly as they look in it. Do not copy anything else from the second image.

BIRTHDAY SET (draw these exactly the same way in every picture):
- On the teacher's head, on top of his camouflage bandana: a red-and-yellow striped cone party hat with a white pom-pom.
- On the teacher's desk (the desk at the front left, next to the chalkboard): a small round white birthday cake with pink icing and three lit candles, on a plate.
- Three balloons (red, yellow, blue) tied with strings to the right corner of the teacher's desk.
- A paper banner with colourful letters "HAPPY BIRTHDAY" hanging on the wall just above the chalkboard.
- A little colourful confetti on the floor at the front of the classroom.

Same pose: he tears the exam paper in two with the same angry grin. Mix a few pieces of birthday confetti into the flying paper scraps. If the teacher's desk is hidden behind him, put the cake on the nearest desk you can see behind him instead.
```

### B8 (optional: the side views, 10 pictures)

These are shown while looking at a neighbour. The same prompt for each of: `left_A.jpeg`, `left_B.jpeg`, `left_C.jpeg`, `left_D.jpeg`, `left_unknown.jpeg`, `right_A.jpeg`, `right_B.jpeg`, `right_C.jpeg`, `right_D.jpeg`, `right_unknown.jpeg`.

- **Upload:** one of them
- **Save as:** the same name with `_birthday` (e.g. `left_B_birthday.jpeg`)

```
Edit the attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs or doors. Keep all existing text unchanged. Only make these changes:

It is the teacher's birthday. Add a couple of balloons (red, yellow, blue) tied to an empty chair in the background and a few pieces of colourful confetti on the floor. Do NOT change the student's exam paper at all: the circled letter or the question mark on it must stay exactly the same, sharp and readable.
```


## The dean's visit (`dean_visit`)

### D1

- **Upload:** `classroom_board_busy.jpeg`
- **Save as:** `classroom_board_busy_dean_visit.jpeg`

```
Edit the attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs, doors, the chalkboard or the exam paper and hands in the foreground. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

DEAN SET (draw these exactly the same way in every picture):
- The teacher dressed up because the dean is visiting: no camouflage bandana, his grey hair neatly combed back; his grey beard neatly trimmed.
- He wears a dark navy suit, a white shirt and a red tie (instead of the black t-shirt and jeans).
- The dean: a stern bald older man with round glasses in a grey suit, peeking in through the window of the door on the right wall.

The teacher is still facing the board, erasing it.
```

### D2

- **Upload:** 1. `classroom_board_watching.jpeg`, 2. `classroom_board_busy_dean_visit.jpeg`
- **Save as:** `classroom_board_watching_dean_visit.jpeg`

```
Edit the first attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs, doors, the chalkboard or the exam paper and hands in the foreground. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

The second image is only a reference: draw the teacher's hair, beard, suit and tie, and the dean, exactly as they look in it. Do not copy anything else from the second image.

DEAN SET (draw these exactly the same way in every picture):
- The teacher dressed up because the dean is visiting: no camouflage bandana, his grey hair neatly combed back; his grey beard neatly trimmed.
- He wears a dark navy suit, a white shirt and a red tie (instead of the black t-shirt and jeans).
- The dean: a stern bald older man with round glasses in a grey suit, peeking in through the window of the door on the right wall.

He faces the class with a strict, hawk-like stare, standing very straight.
```

### D3

- **Upload:** 1. `classroom_desk_busy.jpeg`, 2. `classroom_board_busy_dean_visit.jpeg`
- **Save as:** `classroom_desk_busy_dean_visit.jpeg`

```
Edit the first attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs, doors, the chalkboard or the exam paper and hands in the foreground. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

The second image is only a reference: draw the teacher's hair, beard, suit and tie, and the dean, exactly as they look in it. Do not copy anything else from the second image.

DEAN SET (draw these exactly the same way in every picture):
- The teacher dressed up because the dean is visiting: no camouflage bandana, his grey hair neatly combed back; his grey beard neatly trimmed.
- He wears a dark navy suit, a white shirt and a red tie (instead of the black t-shirt and jeans).
- The dean: a stern bald older man with round glasses in a grey suit, peeking in through the window of the door on the right wall.

Instead of a phone, he is grading a neat stack of papers with a red pen at his desk, head down.
```

### D4

- **Upload:** 1. `classroom_desk_watching.jpeg`, 2. `classroom_board_busy_dean_visit.jpeg`
- **Save as:** `classroom_desk_watching_dean_visit.jpeg`

```
Edit the first attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs, doors, the chalkboard or the exam paper and hands in the foreground. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

The second image is only a reference: draw the teacher's hair, beard, suit and tie, and the dean, exactly as they look in it. Do not copy anything else from the second image.

DEAN SET (draw these exactly the same way in every picture):
- The teacher dressed up because the dean is visiting: no camouflage bandana, his grey hair neatly combed back; his grey beard neatly trimmed.
- He wears a dark navy suit, a white shirt and a red tie (instead of the black t-shirt and jeans).
- The dean: a stern bald older man with round glasses in a grey suit, peeking in through the window of the door on the right wall.

He sits at his desk and looks up at the class with a strict, suspicious stare, a red pen in his hand and a stack of papers on the desk.
```

### D5

- **Upload:** 1. `classroom_warning.jpeg`, 2. `classroom_board_busy_dean_visit.jpeg`
- **Save as:** `classroom_warning_dean_visit.jpeg`

```
Edit the first attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs, doors, the chalkboard or the exam paper and hands in the foreground. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

The second image is only a reference: draw the teacher's hair, beard, suit and tie, and the dean, exactly as they look in it. Do not copy anything else from the second image.

DEAN SET (draw these exactly the same way in every picture):
- The teacher dressed up because the dean is visiting: no camouflage bandana, his grey hair neatly combed back; his grey beard neatly trimmed.
- He wears a dark navy suit, a white shirt and a red tie (instead of the black t-shirt and jeans).
- The dean: a stern bald older man with round glasses in a grey suit, peeking in through the window of the door on the right wall.

He keeps the same furious face and pose, pointing straight at the viewer; his tie is slightly loosened from anger.
```

### D6

- **Upload:** 1. `classroom_caught.png`, 2. `classroom_board_busy_dean_visit.jpeg`
- **Save as:** `classroom_caught_dean_visit.png`

```
Edit the first attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs or doors. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

The second image is only a reference: draw the teacher's hair, beard, suit and tie, and the dean, exactly as they look in it. Do not copy anything else from the second image.

DEAN SET (draw these exactly the same way in every picture):
- The teacher dressed up because the dean is visiting: no camouflage bandana, his grey hair neatly combed back; his grey beard neatly trimmed.
- He wears a dark navy suit, a white shirt and a red tie (instead of the black t-shirt and jeans).
- The dean: a stern bald older man with round glasses in a grey suit, peeking in through the window of the door on the right wall.

Same pose: he tears the exam paper in two with the same angry grin. This time the dean stands in the open doorway on the right, nodding approvingly.
```


## New phone (`new_phone`)

### N1

- **Upload:** `classroom_desk_busy.jpeg`
- **Save as:** `classroom_desk_busy_new_phone.jpeg`

```
Edit the attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs, doors, the chalkboard or the exam paper and hands in the foreground. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

NEW PHONE SET (draw these exactly the same way in every picture):
- In the teacher's hand: a large, shiny, brand-new rose-gold smartphone with a glowing screen.
- On his desk next to him: the open white phone box with its lid leaning against it, a coiled white charger cable and a peeled-off plastic screen film.

He holds the phone with both hands, head bent down close to it, completely absorbed, with a happy little smile; the screen lights up his face.
```

### N2

- **Upload:** 1. `classroom_desk_watching.jpeg`, 2. `classroom_desk_busy_new_phone.jpeg`
- **Save as:** `classroom_desk_watching_new_phone.jpeg`

```
Edit the first attached image. Keep EXACTLY the same camera angle, framing, image size, art style, colours and lighting. Do not move, add or remove any students, desks, chairs, doors, the chalkboard or the exam paper and hands in the foreground. Keep the teacher in exactly the same position, size and pose, with his head in the same place. Keep all existing text unchanged. Only make these changes:

The second image is only a reference: draw the phone, the phone box, the cable and the plastic film exactly as they look in it. Do not copy anything else from the second image.

NEW PHONE SET (draw these exactly the same way in every picture):
- In the teacher's hand: a large, shiny, brand-new rose-gold smartphone with a glowing screen.
- On his desk next to him: the open white phone box with its lid leaning against it, a coiled white charger cable and a peeled-off plastic screen film.

He has just looked up at the class, still holding the new phone in one hand, reluctant to put it down.
```
