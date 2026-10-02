import random as r

d = dict(enumerate([1 for x in range(12)], 1)) # {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1}
d[r.choice(list(d.keys()))] = r.choice([0, 2])
# split d into 1->4 and 5-> 8 and 9->12

def weight(a, b) -> str:
    if sum(a) == sum(b):
        return True
    import random as r


    def weigh(left, right, odd_ball, odd_is_heavy):
        """Return -1 when left is lighter, 0 when balanced, and 1 when heavier."""
        left_weight = len(left)
        right_weight = len(right)

        if odd_ball in left:
            left_weight += 1 if odd_is_heavy else -1
        if odd_ball in right:
            right_weight += 1 if odd_is_heavy else -1

        return (left_weight > right_weight) - (left_weight < right_weight)


    def identify(odd_ball, odd_is_heavy):
        """Identify the odd ball using at most three balance-scale weighings."""
        good_ball = 9

        first = weigh([1, 2, 3, 4], [5, 6, 7, 8], odd_ball, odd_is_heavy)

        if first == 0:
            # 9-12 are candidates, and balls 1-8 are known good.
            second = weigh([9, 10, 11], [1, 2, 3], odd_ball, odd_is_heavy)
            if second == 0:
                result = (12, weigh([12], [good_ball], odd_ball, odd_is_heavy) == 1)
            elif second == 1:
                result = _identify_three([9, 10, 11], odd_ball, odd_is_heavy)
            else:
                result = _identify_three([9, 10, 11], odd_ball, odd_is_heavy, odd_is_heavy=False)
        else:
            # This weighing leaves three candidates in the balance direction,
            # two in the opposite direction, or three when it balances.
            second = weigh([1, 2, 5], [3, 6, 9], odd_ball, odd_is_heavy)
            if second == 1:
                candidates = [1, 2, 6]
                result = _identify_three(candidates, odd_ball, odd_is_heavy, first_direction=1)
            elif second == -1:
                candidates = [3, 5]
                result = _identify_two(candidates, odd_ball, odd_is_heavy, first_direction=1)
            else:
                candidates = [4, 7, 8]
                result = _identify_three(candidates, odd_ball, odd_is_heavy, first_direction=1)

            if first == -1:
                # Reverse heavy/light interpretation when the first pan is lighter.
                result = (result[0], not result[1])

        return result


    def _identify_two(candidates, odd_ball, odd_is_heavy, first_direction=None):
        left, right = candidates
        outcome = weigh([left], [9], odd_ball, odd_is_heavy)
        if outcome == 1:
            return left, True
        return right, False


    def _identify_three(candidates, odd_ball, odd_is_heavy, odd_is_heavy=None, first_direction=None):
        first_candidate, second_candidate, third_candidate = candidates
        outcome = weigh([first_candidate], [second_candidate], odd_ball, odd_is_heavy)
        if outcome == 0:
            return third_candidate, odd_is_heavy is not False
        if outcome == 1:
            return first_candidate, odd_is_heavy is not False
        return second_candidate, odd_is_heavy is not False


    if __name__ == "__main__":
        odd_ball = r.randint(1, 12)
        odd_is_heavy = r.choice([True, False])
        print(f"Target is ball {odd_ball}, and it is {'heavier' if odd_is_heavy else 'lighter'}.")
        print(f"Solver found: ball {identify(odd_ball, odd_is_heavy)}")
