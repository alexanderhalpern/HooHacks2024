import json
import numpy as np

from libs.pymidifile import reformat_midi, mid_to_matrix, matrix_to_mid, quantize_matrix

def judge_attempt(reference_file, user_file):

    # compare the files


def midi_compare(reference_file, user_file):
    reference_midi = quantize_midi(reference_file)
    user_midi = quantize_midi(user_file)

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

    incorrect_pitches = []

    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref_notes[i - 1][0] == user_notes[j - 1][0]:
            # No error, move to previous notes
            i -= 1
            j -= 1
        else:

            # Check for missing or extra notes
            if i > 0 and (j == 0 or dp[i][j - 1] >= dp[i - 1][j]):
                incorrect_pitches.append({
                    "reference_pitch": ref_notes[i - 1][0],
                    "user_pitch": None,
                    "time": sum([msg[1] for msg in ref_notes[:i]])
                })
                i -= 1
            elif j > 0 and (i == 0 or dp[i][j - 1] < dp[i - 1][j]):
                incorrect_pitches.append({
                    "reference_pitch": None,
                    "user_pitch": user_notes[j - 1][0],
                    "time": sum([msg[1] for msg in user_notes[:j]])
                })
                j -= 1

    # now that we have the incorrect pitches, we can figure out the type of error
    # and add it to the errors dictionary
    while len(incorrect_pitches) > 0:
        pitch = incorrect_pitches[0]

        # if the user played a pitch that was not in the reference
        if pitch["reference_pitch"] is None:

            # see if the user played a different pitch at the same time
            also_played = []
            for j in range(1, len(incorrect_pitches)):
                other_pitch = incorrect_pitches[j]
                if other_pitch["time"] == pitch["time"] and other_pitch["reference_pitch"] is not None:
                    also_played.append((other_pitch, abs(other_pitch["reference_pitch"] - pitch["user_pitch"])))

            # if the user played a different pitch at the same time
            if len(also_played) > 0:
                # find the closest pitch
                closest_pitch = min(also_played, key=lambda x: x[1])
                errors["incorrect_pitches"].append({
                    "reference_pitch": closest_pitch[0]["reference_pitch"],
                    "user_pitch": pitch["user_pitch"],
                    "time": pitch["time"]
                })
                # remove the closest pitch from the list
                incorrect_pitches.remove(closest_pitch[0])
                incorrect_pitches.pop(0)

            # if the user played the correct pitch at the wrong time
            # TODO

            # if we didn't find a matching pitch, then the user played an extra note
            else:
                errors["extra_notes"].append({
                    "user_pitch": pitch["user_pitch"],
                    "time": pitch["time"]
                })
                incorrect_pitches.pop(0)

        # if the user missed a pitch that was in the reference
        elif pitch["user_pitch"] is None:

            # if the user played a different pitch at the same time
            also_played = []
            for j in range(1, len(incorrect_pitches)):
                other_pitch = incorrect_pitches[j]
                if other_pitch["time"] == pitch["time"] and other_pitch["user_pitch"] is not None:
                    also_played.append((other_pitch, abs(other_pitch["user_pitch"] - pitch["reference_pitch"])))

            # if the user played a different pitch at the same time
            if len(also_played) > 0:
                # find the closest pitch
                closest_pitch = min(also_played, key=lambda x: x[1])
                errors["incorrect_pitches"].append({
                    "reference_pitch": pitch["reference_pitch"],
                    "user_pitch": closest_pitch[0]["user_pitch"],
                    "time": pitch["time"]
                })
                # remove the closest pitch from the list
                incorrect_pitches.remove(closest_pitch[0])
                incorrect_pitches.pop(0)

            # if we didn't find a matching pitch, then the user missed a note
            else:
                errors["missing_notes"].append({
                    "reference_pitch": pitch["reference_pitch"],
                    "time": pitch["time"]
                })
                incorrect_pitches.pop(0)


    return errors

def clean_midi(mid):
    return reformat_midi(mid, verbose=False, write_to_file=False, override_time_info=True)

def quantize_midi(mid, step_size=0.5):
    reformatted = reformat_midi(mid, verbose=False, write_to_file=False, override_time_info=True)
    matrix = mid_to_matrix(reformatted)
    quantizer = quantize_matrix(matrix, stepSize=0.25, quantizeOffsets=True, quantizeDurations=False)
    return matrix_to_mid(quantizer)



# Example usage
reference_file = "assets/midi/twinkle-twinkle-little-star.mid"
user_file = "assets/midi/twinkle-twinkle-bad.mid"
result = midi_compare(reference_file, user_file)

# save the result to a file with indent
with open("errors.json", "w") as f:
    f.write(json.dumps(result, indent=4))

