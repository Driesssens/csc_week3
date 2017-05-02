import random
from collections import defaultdict
import os
from datetime import datetime


def generate_ballot(n_alternatives):
    return random.sample(list(range(n_alternatives)), n_alternatives)


def generate_profile(n_alternatives, n_voters):
    return [generate_ballot(n_alternatives) for voter in range(n_voters)]


def plurality_scores(profile):
    scores = defaultdict(int)

    for ballot in profile:
        scores[ballot[0]] += 1

    return scores


def borda_scores(profile):
    scores = defaultdict(int)

    for ballot in profile:
        for i in range(len(ballot)):
            position = i + 1
            scores[ballot[i]] += len(ballot) - position

    return scores


def copeland_scores(profile):
    n_alternatives = len(profile[0])
    table = defaultdict(lambda: defaultdict(int))

    for ballot in profile:
        for i_top_alternative in range(n_alternatives):
            for i_bottom_alternative in range(i_top_alternative, n_alternatives):
                table[ballot[i_top_alternative]][ballot[i_bottom_alternative]] += 1

    scores = defaultdict(int)

    for i_alternative in range(n_alternatives):
        for j_alternative in range(i_alternative, n_alternatives):
            balance = 0
            balance += table[i_alternative][j_alternative]
            balance -= table[j_alternative][i_alternative]

            if balance == 0:
                scores[i_alternative] += 0
                scores[j_alternative] += 0
            elif balance > 0:
                scores[i_alternative] += 1
                scores[j_alternative] -= 1
            else:
                scores[i_alternative] -= 1
                scores[j_alternative] += 1

    return scores


def winners(scoring_rule, profile):
    scores = scoring_rule(profile)
    top_score = max(scores.values())
    return [alternative for alternative, score in scores.items() if score == top_score]


def manipulability(scoring_rule, incomplete_profile, favourite_alternative):
    return search_manipulative_ballot(scoring_rule, incomplete_profile, favourite_alternative) is not None


def search_manipulative_ballot(rule, incomplete_profile, favourite_alternative):
    manipulative_ballot = [favourite_alternative]
    other_alternatives = list(range(len(incomplete_profile[0])))
    other_alternatives.remove(favourite_alternative)

    while other_alternatives:  # While we still have positions to fill on the manipulative ballot...
        for considered_alternative in other_alternatives:  # Consider each alternative we haven't positioned yet
            #  Separate considered alternative from the rest
            remaining_other_alternatives = other_alternatives[:]
            remaining_other_alternatives.remove(considered_alternative)

            #  Compute the scores for if we would try to manipulate by placing the considered alternative next on our manipulative ballot
            scores = rule(incomplete_profile + [manipulative_ballot + [considered_alternative] + remaining_other_alternatives])

            if scores[favourite_alternative] < scores[considered_alternative]:
                # Our favourite now loses. Considered alternative no good option for this position on manipulative ballot. Try next.
                continue

            else:
                # This works! Our favourite still wins. Position considered alternative on manipulative ballot.
                manipulative_ballot.append(considered_alternative)
                other_alternatives.remove(considered_alternative)

                # Maybe we got lucky on some other positions as well?
                for remaining_other_alternative in remaining_other_alternatives:

                    if scores[favourite_alternative] < scores[remaining_other_alternative]:
                        # Nope. Our favourite now loses
                        break

                    else:
                        # This works! Our preferred alternative still wins. Position on manipulative ballot.
                        manipulative_ballot.append(remaining_other_alternative)
                        other_alternatives.remove(remaining_other_alternative)

                # Go back to checking if we still need to fill positions on manipulative ballot.
                break
        else:
            # Unfortunately, every alternative we try to add to our manipulative ballot causes our favourite to lose.
            return None

    # Yes! We have constructed a manipulative ballot that causes our favourite to win.
    return manipulative_ballot


class Experiment:
    results_folder = "results"

    def __init__(self, results_file_name=None, debug=False):
        self.debug = debug

        if results_file_name:
            self.results_file_name = results_file_name
        else:
            self.results_file_name = datetime.now

    def manipulable(self, scoring_rule, profile):

        truthful_winners = winners(scoring_rule, profile)

        if self.debug:
            print("Checking the following profile with winners {0}: {1}".format(truthful_winners, profile))

        for i_voter in range(len(profile)):
            truthful_ballot = profile[i_voter]
            for alternative in truthful_ballot:
                if alternative in truthful_winners:
                    if self.debug:
                        print("   As alternative {0} is in set of winners, voter {1} with ballot {2} can not manipulate.".format(alternative, i_voter, truthful_ballot))
                        break
                else:
                    incomplete_profile = profile[:]
                    incomplete_profile.remove(truthful_ballot)
                    manipulative_ballot = search_manipulative_ballot(scoring_rule, incomplete_profile, alternative)

                    if manipulative_ballot:
                        if self.debug:
                            print("   Voter {0} can elect {1} by changing {2} to {3}.".format(i_voter, alternative, truthful_ballot, manipulative_ballot))
                        return True

                    else:
                        if self.debug:
                            print("   Voter {0} with ballot {1} can't manipulate to elect {2}.".format(i_voter, truthful_ballot, alternative))

    def experiment(self, scoring_rule, n_alternatives, n_voters, n_samples):
        n_manipulable = 0
        n_nonmanipulable = 0

        for i_sample in range(n_samples):
            sample_profile = generate_profile(n_alternatives, n_voters)
            if self.manipulable(scoring_rule, sample_profile):
                n_manipulable += 1
            else:
                n_nonmanipulable += 1

        results = "Rule: {0}. Alternatives: {1}. Voters: {2}. Samples: {3}. Manipulable: {4} ({5}%). Nonmanipulable: {6} ({7}%).".format(
            scoring_rule.__name__,
            n_alternatives,
            n_voters,
            n_samples,
            n_manipulable,
            n_manipulable / float(n_samples) * 100,
            n_nonmanipulable,
            n_nonmanipulable / float(n_samples) * 100
        )

        print(results)

        os.makedirs(self.results_folder, exist_ok=True)
        output = open(os.path.join(self.results_folder, self.results_file_name), 'w')
        print(results, file=output)


def test_one_manipulation():
    exp = Experiment()
    print(exp.manipulable(borda_scores, [[0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [1, 0, 2, 3], [3, 2, 1, 0]]))


def test():
    exp = Experiment("first_test")
    exp.experiment(plurality_scores, 4, 4, 100)
    exp.experiment(plurality_scores, 5, 5, 100)
    exp.experiment(plurality_scores, 5, 10, 100)
    exp.experiment(plurality_scores, 10, 5, 100)
    exp.experiment(plurality_scores, 10, 10, 100)
    exp.experiment(plurality_scores, 10, 15, 100)


test()
