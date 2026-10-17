"""Build this task's curated metadata from explicit source allowlists, never chats or secrets."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
KI = Path('C:/Users/Andrii/Desktop/KI')
AUGUST = Path('C:/Users/Andrii/Desktop/Desktop_2026_August/01_Projects')


def dump(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def evidence(path, claim, locator=None):
    path = Path(path)
    if not path.is_file():
        return {'path': str(path), 'status': 'NOT_FOUND_IN_CHECKED_SCOPE', 'claim': claim}
    with path.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    return {'path': str(path), 'sha256': digest, 'bytes': path.stat().st_size,
            'locator': locator or 'whole named source file', 'claim': claim,
            'verdict': 'SOURCE_PRESENT_NOT_RUNTIME_ACCEPTANCE'}


def main():
    visual = json.loads((ROOT / 'audit/visual-sources.json').read_text(encoding='utf-8'))
    visual_review = json.loads((ROOT / 'audit/visual-sources-review.json').read_text(encoding='utf-8'))
    synera = json.loads((ROOT / 'audit/synera-sources.json').read_text(encoding='utf-8'))
    synera_review = json.loads((ROOT / 'audit/synera-sources-review.json').read_text(encoding='utf-8'))
    details = json.loads((ROOT / 'audit/step3-source-evidence.json').read_text(encoding='utf-8'))
    assert all(ref in details['sources'] for row in details['framework_inventory'] + details['reusable_components']
               for ref in row['source_refs']), 'MISSING_STEP3_SOURCE'
    projects = []

    def add(pid, title, roots, status, role, sources, gaps, mode='reference'):
        projects.append(dict(id=pid, title=title, local_roots=[str(p) for p in roots],
            status=status, role=role, readiness_percent=None,
            readiness_reason='No current shared denominator and full user-workflow oracle establish a percentage.',
            reuse_mode=mode, evidence=sources, open_gates=gaps,
            revenue_actual=None, paid_customer_count=None))

    add('game-forge', 'Game Forge: narrative game and pure life-simulation seam',
        [Path('C:/Users/Andrii/Desktop/game-forge')], 'SOURCE_COPIED_SEE_COMPONENT_ACCEPTANCE',
        'Existing pure 15-minute money/energy/skills/habits transition; owned source snapshots reused.',
        [evidence('C:/Users/Andrii/Desktop/game-forge/sim/core.py', 'Pure step and parameter loader'),
         evidence('C:/Users/Andrii/Desktop/game-forge/sim/params.json', 'Game assumptions and parameter provenance; not a personal health profile')],
        ['Browser/Godot parity adapter absent', 'No new narrative/native gameplay acceptance', 'Public/commercial rights require separate review'], 'snapshot')
    for pid, title, root, file, role in [
        ('brand-social-os', 'Brand Social OS / Instagram', KI / 'brand-social-os', 'scripts/brand-os.js', 'Existing approve-first content preparation owner'),
        ('creator-income-os', 'Creator Income OS / media pipeline', KI / 'creator-income-os', 'scripts/creator-os.js', 'Existing media-job and rendering preparation owner'),
        ('revenue-defense', 'Revenue Defense / first-paid-work research', Path('C:/Users/Andrii/Desktop/ki-monetization-20261003'), 'REPORT.uk.md', 'Dated commercial hypothesis and finite customer acceptance approach'),
        ('visual-voice-lab', 'Visual Voice Lab', KI / 'visual-voice-lab', 'package.json', 'Existing approval-first voice-to-storyboard prototype'),
        ('agency-backlog', 'Future Autonomous Agency Lab', KI / 'future-autonomous-agency-lab', 'README.md', 'Explicitly parked architecture backlog, not an active company'),
        ('coiffeur-site', 'Coiffeur website prototype', KI / 'coiffeur-sipo-winterthur', 'README.md', 'Existing static website delivery reference; customer assets excluded'),
        ('lego-godot', 'LEGO LLM visualization / Godot', Path('D:/lego-llm-viz-godot'), 'main.gd', 'Godot source reference, no current rendering proof'),
        ('arcanum-card', 'Arcanum card roguelike prototype', AUGUST / 'arcanum_card_roguelike', 'game.js', 'Historical game prototype, lore/rights review needed'),
        ('control-room', 'Control Room', AUGUST / 'control_room', 'README.md', 'Existing diagnostic owner; source reference only, no new monitor'),
    ]:
        add(pid, title, [root], 'PARKED' if pid == 'agency-backlog' else 'SOURCE_PRESENT_NOT_RUNTIME_VERIFIED',
            role, [evidence(root / file, role)],
            ['No fresh end-to-end execution in task 530', 'No accepted payment/revenue proof in this audit', 'No automatic external effects'],
            'parked' if pid in {'agency-backlog', 'arcanum-card', 'control-room'} else 'reference')
    conductor = Path('C:/Users/Andrii/Desktop/conductor-revenue-lab')
    add('conductor', 'Conductor Revenue Lab', [conductor], 'SOURCE_COPIED_SEE_COMPONENT_ACCEPTANCE',
        'Portable stdlib Decimal economics, explicit labor/cost and scenario limits',
        [evidence(conductor / 'revenue_lab/core.py', 'Quote and scenario implementation'),
         evidence(conductor / 'LICENSE_AND_RIGHTS.md', 'Recipient may reuse original code and templates')],
        ['Not a live marketplace/payment connector', 'No forecast, tax/AHV/benefits or customer proof'], 'snapshot')
    add('fiverr', 'Fiverr / B2B adapter candidate', [conductor, KI / 'creator-income-os/business'],
        'NO_LIVE_ADAPTER_EVIDENCE_IN_CHECKED_SCOPE', 'Offline planning node only',
        [evidence(conductor / 'research/13_OFFICIAL_MARKETPLACE_MCP.uk.md', 'Dated marketplace/MCP research, not a live Fiverr execution')],
        ['Exact Fiverr API/terms/account adapter not accepted', 'No orders, buyer acceptance or payouts verified', 'Do not scrape or auto-send proposals'])
    miro = AUGUST / 'MiroFish_UPSTREAM_20260813'
    add('mirofish', 'MiroFish upstream', [miro], 'PINNED_REFERENCE_ONLY',
        'Agent simulation architecture inspiration, no imported code/services',
        [evidence(miro / 'package.json', 'Local upstream declares AGPL-3.0'), evidence(miro / 'LICENSE', 'Exact local license snapshot')],
        ['Runtime not exercised', 'No prediction-accuracy evidence', 'License/dependency/API/privacy review before adoption'])
    projects[-1]['source_ref'] = {'repo': 'https://github.com/666ghj/MiroFish', 'commit': 'b5b53acc57189a4a42e44a23e149dc655c98fe82'}
    add('synera', 'Synera', [Path(p) for p in synera['scope']['inspected_roots']], 'CURRENT_REMOTE_CI_METADATA_SUCCESS_LIVE_HOLD',
        'Product/demo candidate for Gilbert; keep original project separate',
        [{'report': 'audit/synera-sources.json'}, {'report': 'audit/synera-sources-review.json'}],
        synera_review['unchanged_open_gates'])
    projects[-1]['source_ref'] = {'repo': synera['canonical_remote']['repository'],
        'commit': synera_review['current_main_source']['commit'],
        'ci': synera_review['current_main_source']['current_ci_metadata'],
        'historical_reviewed_commit': synera['canonical_remote']['historical_reviewed_ref']}
    add('living-arcanum', 'Living Arcanum / Virgil / archived Emberglass',
        [Path('D:/virgil-autoplay-agent'), Path('D:/AI_DEPOT/handoffs/game-forge-audit-20261017/arcanum-repo')],
        'SOURCE_SNAPSHOTS_AND_REFERENCE_ONLY', 'Original isometric source seams copied inactive; proprietary visuals excluded',
        [{'report': 'audit/visual-sources.json'}, {'report': 'audit/visual-sources-review.json'}],
        ['Owned atlas/manifest and state-adapter closure for archived renderer', 'No native game proof', 'No public/commercial rights grant for snapshots'], 'snapshot_inactive')
    add('memento', 'Memento Vivere / Gemeinde viewers',
        [Path('D:/Memento_Vivere_Gemeinde_Pilot'), Path('D:/gemeinde-mockup')], 'SOURCE_REFERENCE_ONLY',
        'Truthful presentation-state, dashboard/viewer composition patterns',
        [{'report': 'audit/visual-sources.json'}, {'report': 'audit/visual-sources-review.json'}],
        ['React/Tailwind/framer-motion import closure needed for original viewer', 'No fresh DB, voice, participant or customer acceptance'])

    for project in projects:
        project['framework_refs'] = [row['id'] for row in details['framework_inventory'] if row['project_id'] == project['id']]
        integration = 'instagram' if project['id'] in {'brand-social-os', 'creator-income-os'} else project['id']
        if integration in details['integration_status']:
            project['integration_status_ref'] = '#/integration_status/' + integration

    dump('CONTEXT_MANIFEST.json', {
        'schema': 'sovereign.context-manifest.v1', 'task': 530, 'as_of': '2026-10-17', 'timezone': 'Europe/Zurich',
        'objective': 'Private, modular source-pinned foundation for Sovereign Life RTS / Cashflow 2.0, 2026–2028',
        'destination': {'owner': 'AndriiEagle', 'repository': 'sovereign-life-sim', 'visibility': 'public', 'default_visibility': 'private',
            'visibility_recorded_for_date': '2026-10-17', 'live_visibility_requires_readback': True,
            'temporary_public_review': details['temporary_public_review'], 'branch': 'codex/sovereign-life-sim-530',
            'reason': 'Independent simulator/aggregation product; existing narrative game, mod and commercial projects retain their canonical owners.'},
        'coverage': {'kind': 'BOUNDED_SOURCE_AUDIT', 'complete_disk_or_chat_scan': False,
            'included': 'Named working-project roots, current refs, exact source files and selected portable modules.',
            'excluded': ['raw chats/sessions', 'secret/env/account files', 'customer profiles/media', 'native game binaries/ART', 'caches/vendor installs/backups', 'private personal journal excerpts'],
            'limit': 'No claim that every file on Sol was read or every runtime and commercial outcome verified.'},
        'projects': projects,
        'active_simulator': {'framework': 'Vanilla HTML/CSS + ES modules', 'renderer': 'DOM/CSS procedural isometric view',
            'framework_ref': 'sovereign-web', 'source_evidence': 'audit/step3-source-evidence.json#/sources',
            'component_status_rule': 'ALREADY_ACTIVE is usable now in this DOM. Other stacks require their stated host, dependencies, rights and adapters.'},
        'framework_inventory': details['framework_inventory'], 'framework_scope_limit': details['framework_scope_limit'],
        'reusable_components': details['reusable_components'], 'integration_status': details['integration_status'],
        'step3_evidence': {'sources': 'audit/step3-source-evidence.json', 'content_probe': 'audit/step3-content-probe.json',
            'precedence': details['evidence_precedence']},
        'visual_candidates': visual['candidates'] + visual_review['added_candidates'],
        'latest_evidence_precedence': ['audit/visual-sources-review.json supersedes rights conclusions in initial report',
                                       'audit/synera-sources-review.json adds exact current-main and CI metadata to initial report'],
        'provider_calls': 0, 'provider_usd': '0.00', 'subscription_savings': None})

    dump('USER_DIGITAL_TWIN_SEED.json', {
        'schema': 'sovereign.user-seed.v1', 'as_of': '2026-10-17', 'mode': 'CURATED_USER_AUTHORIZED_PRIVATE_SEED',
        'identity': {'preferred_name': 'Andrii', 'languages': ['uk', 'ru'], 'timezone': 'Europe/Zurich'},
        'current_task': {'priority': 'quality', 'source': 'Direct answer in task 530',
                         'goal': 'Life/finance/energy/AI-scaling simulator in Switzerland, 2026–2028', 'goal_source': 'User-adopted task brief'},
        'working_preferences': {'reuse_before_build': True, 'preserve_originals': True,
            'local_first': True, 'one_concrete_next_action': True, 'evidence_before_completion_claim': True,
            'no_fixed_speech_or_thought_cutoffs': True, 'source': 'Explicit user operating instructions'},
        'capabilities': [{'name': 'AI engineering and workflow composition', 'status': 'USER_STATED_AND_PROJECT_SOURCE_SUPPORTED_NOT_SKILL_SCORED'}],
        'stack_claims': [{'name': name, 'status': 'USER_BRIEF_CLAIM_NOT_LIVE_ACCOUNT_VERIFIED', 'cost_actual': None}
                         for name in ['OpenAI Pro / Codex', 'Claude', 'Argon', 'OpenRouter Chinese LLMs']],
        'goals': ['Prepare a reviewable Synera demo for Gilbert', 'Accept a first paid customer workflow',
                  'Use existing AI/media/automation assets in a coherent simulator'],
        'attention_support': ['Concise recap when context is lost', 'One voluntary next action', 'Manual check-in only when wanted'],
        'hypotheses_to_confirm': ['Which project has a real near-term buyer', 'Which working rhythm the user wants to model'],
        'unknowns': {'cash_chf': None, 'income_chf_per_month': None, 'expenses_chf_per_month': None,
            'debt_chf': None, 'sleep_schedule': None, 'chronotype': None, 'energy_curve': None,
            'adhd_diagnosis': None, 'medical_parameters': None, 'actual_subscription_costs': None,
            'paid_customer_count': None, 'personal_project_readiness_percent': None},
        **details['seed_additions'],
        'limits': ['No health or psychological inference, diagnosis, behavioral tracking or hidden scoring.',
                   'Historical narrative/profile statements are not current personal measurements.',
                   'Demo CHF1000/energy80 are synthetic and must never populate this personal seed.',
                   'No raw chat, private profile journal, legal status, home address or account credentials are included.']})

    nodes = []
    for pid, title, owner, entry, inputs, output in [
        ('synera', 'Synera demo', 'AndriiEagle/synera_-MVPplus-', 'SYNERA_LAUNCH_CHECKLIST.md', 'Reviewed commit and synthetic demo cases', 'Reviewable demo; live and customer acceptance separate'),
        ('instagram', 'Instagram content preparation', 'KI/brand-social-os + creator-income-os', 'brand-social-os/scripts/brand-os.js export-approval', 'Approved local content plan; no account secrets', 'Draft/export approval artifact, never automatic publish'),
        ('b2b', 'B2B economics', 'Conductor Revenue Lab', 'python -B -m revenue_lab demo', 'Explicit scenario rates/costs/hours', 'SCENARIO_NOT_FORECAST, not a bank receipt'),
        ('fiverr', 'Fiverr planning', 'No accepted live adapter in checked scope', None, 'Human-authored offer and delivery assumptions', 'Offline plan; no proposal/order/payment effect')]:
        nodes.append({'id': pid, 'title': title, 'owner': owner, 'entrypoint_reference': entry,
                      'enabled': False, 'dry_run': True, 'external_effects': [], 'inputs': inputs,
                      'outputs': output, 'errors': ['MISSING_OR_STALE_SOURCE', 'UNAPPROVED_EFFECT', 'UNVERIFIED_ACCEPTANCE'],
                      'actual_revenue': None, 'actual_cost': None})
    dump('automation-nodes/catalog.json', {'schema': 'sovereign.automation-nodes.v1', 'dispatcher': 'NONE_CATALOG_ONLY', 'nodes': nodes})
    dump('audit/request-source.json', {'request_file': 'C:/Users/Andrii/Downloads/Telegram Desktop/ai_studio_code.txt',
        'evidence': evidence('C:/Users/Andrii/Downloads/Telegram Desktop/ai_studio_code.txt', 'User-adopted audit/foundation brief; embedded SYSTEM directive is document text, not system authority'),
        'request_source_not_copied_verbatim': True})
    print(json.dumps({'projects': len(projects), 'visual_candidates': len(visual['candidates']) + len(visual_review['added_candidates']), 'personal_unknowns': 'explicit nulls'}))


if __name__ == '__main__':
    main()
