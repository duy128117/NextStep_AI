import os
import sys
from importlib import import_module

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)


def main() -> None:
    session_module = import_module("app.db.session")
    skill_module = import_module("app.models.skill")
    job_skill_module = import_module("app.models.job_skill")
    normalization_module = import_module("app.services.skill_normalization")

    db = session_module.get_standalone_db()
    Skill = skill_module.Skill
    JobSkill = job_skill_module.JobSkill
    expand_skill_labels = normalization_module.expand_skill_labels
    canonicalize_skill_key = normalization_module.canonicalize_skill_key
    is_non_skill_role_label = normalization_module.is_non_skill_role_label

    split_rows = 0
    inserted_rows = 0
    deactivated_skills = 0

    try:
        skills = db.query(Skill).all()
        skill_by_key = {
            canonicalize_skill_key(skill.name): skill
            for skill in skills
            if skill.name
        }

        rows = db.query(JobSkill).all()
        for row in rows:
            if not row.skill or not row.skill.name:
                continue

            original_name = row.skill.name
            expanded = [
                name
                for name in expand_skill_labels(original_name)
                if name and not is_non_skill_role_label(name)
            ]
            original_key = canonicalize_skill_key(original_name)
            expanded_keys = {canonicalize_skill_key(name) for name in expanded if canonicalize_skill_key(name)}

            if len(expanded_keys) <= 1 and original_key in expanded_keys:
                continue

            for skill_name in expanded:
                key = canonicalize_skill_key(skill_name)
                if not key:
                    continue

                skill = skill_by_key.get(key)
                if not skill:
                    skill = Skill(name=skill_name, category="technical", aliases=[], is_active=True)
                    db.add(skill)
                    db.flush()
                    skill_by_key[key] = skill

                exists = (
                    db.query(JobSkill)
                    .filter(
                        JobSkill.job_job_id == row.job_job_id,
                        JobSkill.skill_skill_id == skill.skill_id,
                    )
                    .first()
                )
                if exists:
                    continue

                db.add(
                    JobSkill(
                        job_job_id=row.job_job_id,
                        skill_skill_id=skill.skill_id,
                        importance=row.importance,
                        evidence_snippet=row.evidence_snippet,
                    )
                )
                inserted_rows += 1

            db.delete(row)
            split_rows += 1

        db.flush()
        for skill in skills:
            if not skill.name:
                continue
            expanded = expand_skill_labels(skill.name)
            if len({canonicalize_skill_key(name) for name in expanded}) > 1 and skill.is_active:
                skill.is_active = False
                deactivated_skills += 1

        db.commit()
        print(f"compound job_skill rows split: {split_rows}")
        print(f"component job_skill rows inserted: {inserted_rows}")
        print(f"compound skills deactivated: {deactivated_skills}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
