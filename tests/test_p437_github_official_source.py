"""P4.37: pinned public GitHub repo metadata, never company financial evidence."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/research"))
import p437_official_github_repo_probe as probe


def sample(name,repo_id,homepage):
    return {"id":repo_id,"full_name":name,"name":name.split("/")[1],
            "owner":{"login":"plausible","type":"Organization"},
            "html_url":"https://github.com/"+name,"homepage":homepage,
            "private":False,"fork":False,"archived":False,"disabled":False,
            "created_at":"2018-12-01T00:00:00Z","updated_at":"2026-10-08T12:00:00Z",
            "pushed_at":"2026-10-08T11:00:00Z","stargazers_count":28000,
            "forks_count":1800,"open_issues_count":25}


class OfficialGitHub(unittest.TestCase):
    def test_policy_and_two_pinned_repos(self):
        probe.check_policy()
        self.assertEqual(len(probe.TARGETS),2)
        self.assertEqual([r[1] for r in probe.TARGETS],[160427405,270703311])

    def test_identity_checks_and_not_financial(self):
        target=probe.TARGETS[0]
        item=sample(*target)
        row=probe.extract_metadata(item,*target)
        self.assertEqual(row["repo_id"],160427405)
        self.assertFalse(row["financial_evidence_verified"])
        self.assertFalse(row["legal_entity_verified"])
        self.assertFalse(row["customers_verified"])
        self.assertFalse(row["eligible_for_publication"])
        for key,value in (("id",999),("private",True),("fork",True),
                          ("archived",True),("homepage","https://other.example")):
            changed=sample(*target)
            changed[key]=value
            with self.assertRaises(ValueError):
                probe.extract_metadata(changed,*target)
        changed=sample(*target)
        changed["owner"]["login"]="unrelated"
        with self.assertRaises(ValueError):
            probe.extract_metadata(changed,*target)

    def test_numeric_validation(self):
        target=probe.TARGETS[1]
        for value in (-1,"100",True,100000001):
            row=sample(*target)
            row["stargazers_count"]=value
            with self.assertRaises(ValueError):
                probe.extract_metadata(row,*target)

    def test_offline_fixtures_are_never_live(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            for target in probe.TARGETS:
                name,rid,home=target
                (folder/(name.replace("/","__")+".json")).write_text(
                    json.dumps(sample(*target)),encoding="utf-8")
            report=probe.collect(folder,False)
            self.assertEqual(report["mode"],"OFFLINE_FIXTURE_NOT_LIVE")
            self.assertEqual(report["requests_attempted"],0)
            self.assertEqual(report["validated_repos"],2)
            self.assertEqual(report["financial_claims_verified"],0)
            self.assertFalse(report["publication_allowed"])

    def test_online_bounded_and_rate_limit_refusal(self):
        def fetch(name,token):
            target=next(x for x in probe.TARGETS if x[0]==name)
            return sample(*target),"a"*64
        with patch.object(probe,"fetch_once",side_effect=fetch) as mock:
            result=probe.collect(online=True)
            self.assertEqual(mock.call_count,2)
            self.assertEqual(result["validated_repos"],2)
        with patch.object(probe,"fetch_once",side_effect=RuntimeError("GITHUB_HTTP_429")) as mock:
            result=probe.collect(online=True)
            self.assertEqual(mock.call_count,1)
            self.assertEqual(result["validated_repos"],0)
            self.assertEqual(result["failures"][0]["reason_code"],"GITHUB_HTTP_429")

    def test_specific_fail_closed_identity_failure_categories(self):
        target = probe.TARGETS[0]
        cases = [
            ("id", 1, "GITHUB_PINNED_REPO_ID_MISMATCH"),
            ("homepage", "https://wrong.example", "GITHUB_HOMEPAGE_MISMATCH"),
            ("private", True, "GITHUB_REPO_POLICY_MISMATCH"),
            ("pushed_at", "invalid", "GITHUB_TIMESTAMP_INVALID"),
            ("stars", None, None),
        ]
        for key, value, code in cases:
            if code is None:
                continue
            with self.subTest(key=key):
                obj = sample(*target)
                obj[key] = value
                with self.assertRaises(ValueError) as context:
                    probe.extract_metadata(obj, *target)
                self.assertEqual(probe._category(context.exception), code)

    def test_safe_transport_diagnostics_do_not_expand_request_cap(self):
        cases = [
            ("GITHUB_RESPONSE_ENVELOPE_REJECTED", "GITHUB_RESPONSE_ENVELOPE_REJECTED"),
            ("GITHUB_REDIRECT_REJECTED", "GITHUB_REDIRECT_REJECTED"),
            ("GITHUB_JSON_ROOT_INVALID", "GITHUB_JSON_ROOT_INVALID"),
            ("Invalid GitHub counter: stargazers_count", "GITHUB_COUNTER_INVALID"),
        ]
        for raw_error, code in cases:
            self.assertEqual(probe._category(ValueError(raw_error)), code)
        with patch.object(probe, "fetch_once",
                          side_effect=ValueError("GITHUB_RESPONSE_ENVELOPE_REJECTED")) as mocked:
            report = probe.collect(online=True)
            self.assertEqual(mocked.call_count, 2)
            self.assertEqual(report["validated_repos"], 0)
            self.assertEqual(report["requests_attempted"], 2)
            self.assertEqual(report["requests_max"], 2)
            self.assertEqual([f["reason_code"] for f in report["failures"]],
                             ["GITHUB_RESPONSE_ENVELOPE_REJECTED"] * 2)
            self.assertFalse(report["publication_allowed"])
            self.assertFalse(report["raw_response_archived"])

    def test_private_output_and_existing_schedule(self):
        with self.assertRaises(ValueError):
            probe.private_path(ROOT/"web/dist/repo-metrics.json")
        wf=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 0 * * *'"),1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"),1)
        self.assertNotIn("cron: '55 */6 * * *'",wf)
        self.assertIn("github.event.schedule == '55 0 * * *'",wf)
        self.assertNotIn("date -u +%H",wf)
        self.assertEqual(wf.count("p437_official_github_repo_probe.py --online"),1)
        self.assertIn("p437_github_metrics.json",wf)
        self.assertIn("p436_unattended_guard.py",wf)
        self.assertIn("retention-days: 2",wf)


if __name__=="__main__":
    unittest.main()
