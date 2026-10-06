from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.pet import Pet
from app.models.user import User


def get_dashboard_stats(db: Session) -> dict:
    """首页统计数据"""
    pet_total = db.query(Pet).count()
    pet_waiting = db.query(Pet).filter(Pet.status == 1).count()
    pet_adopted = db.query(Pet).filter(Pet.status == 0).count()
    user_total = db.query(User).count()

    # 物种分布
    species_rows = db.query(Pet.species, func.count(Pet.id)).group_by(Pet.species).all()
    species_distribution = [
        {"name": name or "未知", "value": count} for name, count in species_rows
    ]

    # 最近 7 天新增趋势
    pet_trend = []
    today = datetime.now().date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = (
            db.query(Pet)
            .filter(Pet.create_time >= day, Pet.create_time < next_day)
            .count()
        )
        pet_trend.append({"date": day.strftime("%m-%d"), "count": count})

    # 最近添加的宠物
    recent = db.query(Pet).order_by(Pet.id.desc()).limit(5).all()
    recent_pets = [
        {
            "id": p.id,
            "name": p.name,
            "species": p.species,
            "img": p.img,
            "status": p.status,
        }
        for p in recent
    ]

    return {
        "pet_total": pet_total,
        "pet_waiting": pet_waiting,
        "pet_adopted": pet_adopted,
        "user_total": user_total,
        "pet_trend": pet_trend,
        "species_distribution": species_distribution,
        "recent_pets": recent_pets,
    }
