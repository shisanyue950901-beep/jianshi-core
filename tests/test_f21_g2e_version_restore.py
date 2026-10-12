"""G2-E restore parity checks. Local model and SQL contract; NOT live positive E2E."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/qa"))
from f21_g2d_cms_offline_model import OfflineCms, Rejected

AUTHOR="SYNTHETIC_AUTHOR"
OTHER="SYNTHETIC_OTHER"
REVIEWER="SYNTHETIC_REVIEWER"
PUBLISHER="SYNTHETIC_PUBLISHER"
KEY="SYNTHETIC_ARTICLE_01"
def rid(n): return f"SYNTHETIC_REQUEST_{n}"

def fixture(ready=True):
    cms=OfflineCms(simulated_gates_ready=ready)
    for user,role in [(AUTHOR,"EDITOR"),(OTHER,"EDITOR"),(REVIEWER,"REVIEWER"),(PUBLISHER,"PUBLISHER")]:
        cms.grant_synthetic(user,role)
    if ready:
        cms.create(AUTHOR,KEY,"SOLUTION_GUIDE",{"title":"合成版本一"},["SYNTHETIC_SOURCE_ONE"],rid(1))
        cms.edit(AUTHOR,KEY,1,{"title":"合成版本二"},["SYNTHETIC_SOURCE_TWO"],True,True,rid(2))
        cms.edit(AUTHOR,KEY,2,{"title":"合成版本三"},["SYNTHETIC_SOURCE_THREE"],True,True,rid(3))
    return cms

def denied(tc,cms,code,fn):
    before=deepcopy(cms.items)
    with tc.assertRaises(Rejected) as e: fn()
    tc.assertEqual(e.exception.code,code)
    tc.assertEqual(cms.items,before)

class G2EVersionRestore(unittest.TestCase):
    def test_history_is_append_only_and_reattestations_reset(self):
        cms=fixture()
        old=deepcopy(cms.items[KEY].versions)
        self.assertEqual(cms.restore_revision(AUTHOR,KEY,3,1,rid(4)),4)
        item=cms.items[KEY]
        self.assertEqual(item.state,"DRAFT")
        self.assertEqual(item.revision,4)
        self.assertEqual({k:v for k,v in item.versions.items() if k<=3},old)
        self.assertEqual(item.versions[4].content["title"],"合成版本一")
        self.assertFalse(item.versions[4].rights)
        self.assertFalse(item.versions[4].facts)
        self.assertEqual(item.events[-1][0],"RESTORE")
        self.assertEqual(len(item.snapshots),0)
        # Explicit fresh editor attestations, then independent reviewer.
        self.assertEqual(cms.edit(AUTHOR,KEY,4,{"title":"合成版本一已复核"},
                                  ["SYNTHETIC_SOURCE_RECHECKED"],True,True,rid(5)),5)
        self.assertEqual(cms.transition(AUTHOR,KEY,5,"IN_REVIEW",rid(6)),6)
        self.assertEqual(cms.transition(REVIEWER,KEY,6,"APPROVED",rid(7)),7)

    def test_restore_rejects_forged_author_stale_current_future_and_duplicate(self):
        cases=[
            ("CMS_OWNER_DENIED",lambda cms: cms.restore_revision(OTHER,KEY,3,1,rid(4))),
            ("CMS_STALE_REVISION",lambda cms: cms.restore_revision(AUTHOR,KEY,2,1,rid(4))),
            ("CMS_INVALID_SOURCE_REVISION",lambda cms: cms.restore_revision(AUTHOR,KEY,3,3,rid(4))),
            ("CMS_INVALID_SOURCE_REVISION",lambda cms: cms.restore_revision(AUTHOR,KEY,3,0,rid(4))),
            ("CMS_DUPLICATE_REQUEST",lambda cms: cms.restore_revision(AUTHOR,KEY,3,1,rid(3))),
        ]
        for code,action in cases:
            with self.subTest(code=code):
                cms=fixture()
                denied(self,cms,code,lambda:action(cms))

    def test_approved_or_inreview_are_immutable_until_rejected(self):
        cms=fixture()
        cms.transition(AUTHOR,KEY,3,"IN_REVIEW",rid(4))
        denied(self,cms,"CMS_RESTORE_REQUIRES_DRAFT",
               lambda: cms.restore_revision(AUTHOR,KEY,4,1,rid(5)))
        cms.transition(REVIEWER,KEY,4,"REJECTED",rid(5))
        self.assertEqual(cms.restore_revision(AUTHOR,KEY,5,1,rid(6)),6)
        self.assertEqual(cms.items[KEY].state,"DRAFT")
        self.assertIsNone(cms.items[KEY].last_reviewer)

    def test_closed_gates_and_old_unsafe_alias_stay_denied(self):
        cms=fixture(False)
        denied(self,cms,"CMS_WRITE_DISABLED",
               lambda: cms.restore_revision(AUTHOR,KEY,3,1,rid(4)))
        cms=fixture()
        denied(self,cms,"CMS_VERSION_ROLLBACK_NOT_IMPLEMENTED",
               lambda: cms.restore_old_revision(KEY,1))

    def test_no_unreviewed_published_snapshot_restore(self):
        cms=fixture()
        cms.items[KEY].snapshots=[{"revision":2,"lifecycle":"STAGED","public":{}}]
        denied(self,cms,"CMS_ACTIVE_PUBLICATION_BLOCKS_RESTORE",
               lambda: cms.restore_revision(AUTHOR,KEY,3,1,rid(4)))

    def test_schema_restore_only_additive_and_server_role(self):
        text=(ROOT/"db/migrations/0057_jianshi_cms_historical_draft_restore.sql").read_text()
        assert_fragments=[
            "create or replace function jianshi_cms.restore_draft_revision(",
            "language plpgsql security invoker","set search_path = ''",
            "perform jianshi_cms.ensure_write_gate(p_actor, array['EDITOR'])",
            "for update","CMS_OWNER_DENIED","CMS_STALE_REVISION",
            "CMS_DUPLICATE_REQUEST","CMS_ACTIVE_PUBLICATION_BLOCKS_RESTORE",
            "v_item.workflow_state not in ('DRAFT','REJECTED')",
            "p_source_revision >= v_item.current_revision",
            "rights_declared, facts_checked","false, false",
            "workflow_state = 'DRAFT'","last_reviewer_id = null",
            "last_edit_at = now()","'RESTORE'","'DRAFT'",
            "from PUBLIC, anon, authenticated","to service_role",
        ]
        for snippet in assert_fragments:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet,text)
        for forbidden in ("create policy","alter table ","drop table ","truncate ",
                          "grant execute to authenticated","account_auth',true",
                          "cms_editor',true"):
            self.assertNotIn(forbidden,text.lower())
        self.assertNotIn("SECURITY DEFINER",text.upper())

if __name__=="__main__":
    unittest.main()
