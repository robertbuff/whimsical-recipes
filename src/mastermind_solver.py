import random
import itertools

colors = ["Red", "Green", "Blue", "Yellow", "White", "Black"]
random.shuffle(colors)
possiblePermutations = list(itertools.permutations(colors, 4))
random.shuffle(possiblePermutations)
evidence = []
location_and_color_matches = None
for permutation in possiblePermutations:
    isCandidate = all(map(
        lambda e: \
            e[1] == sum(x == y for x, y in zip(e[0], permutation)) and \
            e[2] == sum(x in permutation for x in e[0]),
        evidence))
    if isCandidate:
        print(permutation)
        location_and_color_matches = int(input("How many exact matches in color and location? "))
        color_but_not_location_matches = int(input("How many matches in color only, but not location? "))
        evidence.append([
            permutation,
            location_and_color_matches,
            location_and_color_matches + color_but_not_location_matches
        ])
if location_and_color_matches != 4:
    print("Hey, you cheated with your evaluations!")
