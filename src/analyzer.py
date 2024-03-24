import json
import mido
import numpy as np

from libs.pymidifile import reformat_midi, mid_to_matrix, matrix_to_mid, quantize_matrix

class Analyzer:
    def __init__(self, judgement_level="beginner"):
        self.judgement_level = judgement_level
        pass


    # is user input good enough
    def judge_attempt(self, reference_midi, user_midi):

        # compare the files
        errors = self.midi_compare(reference_midi, user_midi)

        sufficient = True
        match self.judgement_level:
            case "beginner":
                # beginners are not allowed to play incorrect notes or have severe timing issues
                if len(errors["incorrect_pitches"]) > 0:
                    sufficient = False
                if len(errors["timing_issues"]) > 1:
                    for issue in errors["timing_issues"]:
                        if abs(issue["reference_time"] - issue["time"]) > 100: # TODO: find a good threshold
                            sufficient = False
                            break

            case "intermediate":
                pass

        return sufficient, errors


    # create a timeline of what mistake(s) were made when
    def error_timeline(self, errors):

        grouped_errors = {}
        for key in errors:
            for error in errors[key]:
                if error["time"] in grouped_errors:
                    grouped_errors[error["time"]]["errors"].append((key, error))
                    if key in grouped_errors[error["time"]]["types"]:
                        grouped_errors[error["time"]]["types"][key] += 1
                    else:
                        grouped_errors[error["time"]]["types"][key] = 1
                else:
                    grouped_errors[error["time"]] = {"errors": [(key, error)], "types": {key: 1}}

        # classify each event as "wrong_notes", "early_timing", "late_timing", "missing_notes", "extra_notes"
        for time in grouped_errors:

            # if all the errors at this time are the same type, then we can classify the event as that type
            if len(grouped_errors[time]["types"]) == 1:
                error_type = list(grouped_errors[time]["types"].keys())[0]

                if error_type == "timing_issues":
                    if grouped_errors[time]["errors"][0][1]["reference_time"] > grouped_errors[time]["errors"][0][1]["time"]:
                        error_type = "early_timing"
                    else:
                        error_type = "late_timing"

                grouped_errors[time]["type"] = error_type

            # if there are multiple types of errors at this time, then we can classify the event as "wrong_notes"
            else:
                grouped_errors[time]["type"] = "wrong_notes"

        return grouped_errors



    # find all the mistakes
    def midi_compare(self, reference_file, user_file):
        reference_midi = self.quantize_midi(reference_file)
        user_midi = self.quantize_midi(user_file)

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

                i -= 1
                j -= 1
                continue

                # check for timing issues (notes are played too far from the reference)
                if abs(ref_notes[i - 1][1] - user_notes[j - 1][1]) > 0: # TODO: find a good threshold

                    # if, in the reference, there are two notes of the same pitch played in a row
                    if i > 1 and ref_notes[i - 1][0] == ref_notes[i - 2][0]:

                        # check if the user got the other note right (if not, it's a timing issue)
                        if j > 1 and user_notes[j - 2][0] == ref_notes[i - 2][0]:
                            i -= 1
                            j -= 1
                            continue

                        errors["timing_issues"].append({
                            "reference_pitch": ref_notes[i - 1][0],
                            "reference_time": ref_notes[i - 1][1],
                            "time": user_notes[j - 1][1]
                        })

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
                    if closest_pitch[0]["reference_pitch"] != pitch["user_pitch"]:
                        errors["incorrect_pitches"].append({
                            "reference_pitch": closest_pitch[0]["reference_pitch"],
                            "user_pitch": pitch["user_pitch"],
                            "time": pitch["time"]
                        })
                    # remove the closest pitch from the list
                    incorrect_pitches.remove(closest_pitch[0])
                    incorrect_pitches.pop(0)


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
                    if closest_pitch[0]["user_pitch"] != pitch["reference_pitch"]:
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

        # look through missing/extra notes to see if they were just played at the wrong time
        return errors

        i = 0
        while i < len(errors["missing_notes"]):
            missing_note = errors["missing_notes"][i]
            for j in range(len(errors["extra_notes"])):
                extra_note = errors["extra_notes"][j]
                if abs(missing_note["time"] - extra_note["time"]) < 400 and missing_note["reference_pitch"] == extra_note["user_pitch"]:
                    errors["timing_issues"].append({
                        "reference_pitch": missing_note["reference_pitch"],
                        "reference_time": missing_note["time"],
                        "time": extra_note["time"],
                    })
                    errors["missing_notes"].pop(i)
                    errors["extra_notes"].pop(j)
                    i -= 1
                    break
            i += 1

        return errors

    def clean_midi(self, mid):
        return reformat_midi(mid, verbose=False, write_to_file=False, override_time_info=True)

    def quantize_midi(self, mid, step_size=0.5):
        reformatted = reformat_midi(mid, verbose=False, write_to_file=False, override_time_info=True)
        matrix = mid_to_matrix(reformatted)
        quantizer = quantize_matrix(matrix, stepSize=0.25, quantizeOffsets=True, quantizeDurations=False)
        return matrix_to_mid(quantizer)

if __name__ == '__main__':
    # Example usage
    analyzer = Analyzer()
    reference_file = "../assets/midi/twinkle-twinkle-little-star.mid"
    user_file = "../assets/midi/twinkle-twinkle-extra-missing-shifted.mid"
    judgement, errors = analyzer.judge_attempt(reference_file, user_file)

    # save the result to a file with indent
    with open("errors.json", "w") as f:
        f.write(json.dumps(errors, indent=4))