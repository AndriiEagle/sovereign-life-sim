"""Explicit toy strategies, no classification of real people or promised returns."""
from contracts import keys, number

STRATEGIES = ('Unconditional_Rescuer', 'Exploitative_Narcissist', 'Sovereign_TitForTat')


def simulate(left='Unconditional_Rescuer', right='Exploitative_Narcissist', rounds=20,
             exit_on_breach=False, payoffs=None, energy_cost=1, exploitation_cost=2):
    if left not in STRATEGIES or right not in STRATEGIES or type(exit_on_breach) is not bool:
        raise ValueError('UNKNOWN_STRATEGY_OR_EXIT_POLICY')
    number(rounds, 'ROUNDS', 1, 500, True)
    number(energy_cost, 'ENERGY_COST', 0, 100)
    number(exploitation_cost, 'EXPLOITATION_COST', 0, 100)
    p = dict(T=5, R=3, P=1, S=0) if payoffs is None else dict(keys(payoffs, ['T','R','P','S'], ['T','R','P','S']))
    for value in p.values():
        number(value, 'PAYOFF', -100, 100)
    if not p['T'] > p['R'] > p['P'] > p['S']:
        raise ValueError('PAYOFF_ORDER_REQUIRES_T_R_P_S')
    history, total, energy, exploited = [], [0,0], [0,0], [0,0]
    def action(strategy, previous):
        if strategy == STRATEGIES[0]: return 'C'
        if strategy == STRATEGIES[1]: return 'D'
        return previous or 'C'
    previous = [None, None]
    for index in range(rounds):
        moves = [action(left, previous[1]), action(right, previous[0])]
        scores = ([p['R'],p['R']] if moves == ['C','C'] else [p['P'],p['P']] if moves == ['D','D']
                  else [p['S'],p['T']] if moves == ['C','D'] else [p['T'],p['S']])
        for i in range(2):
            hit = moves[i] == 'C' and moves[1-i] == 'D'
            exploited[i] += int(hit)
            energy[i] += energy_cost + exploitation_cost * hit
            total[i] += scores[i]
        history.append(dict(round=index+1, actions=moves, payoff=scores, cumulative=list(total), energy=list(energy)))
        previous = moves
        if exit_on_breach and moves[1] == 'D': break
    return dict(status='SCENARIO_NOT_DIAGNOSIS_OR_GUARANTEE', strategies=[left,right],
                requested_rounds=rounds, completed_rounds=len(history), payoffs=p,
                energy_cost=energy_cost, exploitation_cost=exploitation_cost,
                exit_on_breach=exit_on_breach, cumulative=total, energy=energy,
                exploitation_rate=[x/len(history) for x in exploited], history=history)


def comparison(rounds=20):
    return [simulate(left=strategy, rounds=rounds) for strategy in (STRATEGIES[0],STRATEGIES[2])] + [
        simulate(left=STRATEGIES[2], rounds=rounds, exit_on_breach=True)]
