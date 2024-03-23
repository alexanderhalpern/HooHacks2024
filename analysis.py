import mido
import json
import numpy as np

def midi_compare(reference_file, user_file):
    reference_midi = mido.MidiFile(reference_file)
    user_midi = mido.MidiFile(user_file)

    errors = {
        "incorrect_pitches": [],
        "timing_issues": [],
        "missing_notes": [],
        "extra_notes": []
    }


    ref_ticks = 0
    user_ticks = 0

    ref_track = reference_midi.merged_track
    user_track = user_midi.merged_track

    ref_notes = []
    user_notes = []

    for msg in ref_track:
        if msg.type == 'note_on':
            ref_notes.append((msg.note, msg.time))

    for msg in user_track:
        if msg.type == 'note_on':
            user_notes.append((msg.note, msg.time))

    # Dynamic programming to find optimal alignment
    dp = np.zeros((len(ref_notes) + 1, len(user_notes) + 1))
    for i in range(len(ref_notes) + 1):
        for j in range(len(user_notes) + 1):
            if i == 0 or j == 0:
                dp[i][j] = i + j
            elif ref_notes[i - 1][0] == user_notes[j - 1][0]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    # Traceback to find alignment and report errors
    i = len(ref_notes)
    j = len(user_notes)
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref_notes[i - 1][0] == user_notes[j - 1][0]:
            # No error, move to previous notes
            i -= 1
            j -= 1
        else:
            # Check for missing or extra notes
            if i > 0 and (j == 0 or dp[i][j - 1] >= dp[i - 1][j]):
                errors["incorrect_pitches"].append({
                    "reference_pitch": ref_notes[i - 1][0],
                    "user_pitch": None,
                    "time": sum([msg[1] for msg in ref_notes[:i]])
                })
                i -= 1
            elif j > 0 and (i == 0 or dp[i][j - 1] < dp[i - 1][j]):
                errors["incorrect_pitches"].append({
                    "reference_pitch": None,
                    "user_pitch": user_notes[j - 1][0],
                    "time": sum([msg[1] for msg in user_notes[:j]])
                })
                j -= 1

    # Report timing issues
    for k in range(i):
        errors["timing_issues"].append({
            "reference_time": sum([msg[1] for msg in ref_notes[:i]]),
            "user_time": 0,
            "time": sum([msg[1] for msg in user_notes[:j]])
        })

    for k in range(j):
        errors["timing_issues"].append({
            "reference_time": 0,
            "user_time": sum([msg[1] for msg in user_notes[:j]]),
            "time": sum([msg[1] for msg in user_notes[:j]])
        })


    return json.dumps(errors)

# Example usage
reference_file = "assets/midi/twinkle-twinkle-little-star.mid"
user_file = "assets/midi/twinkle-twinkle-wrong-pitches.mid"
result = midi_compare(reference_file, user_file)

# save the result to a file with indent
with open("mistakes.json", "w") as f:
    f.write(json.dumps(json.loads(result), indent=4))

