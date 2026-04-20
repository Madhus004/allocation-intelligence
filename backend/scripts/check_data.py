from sqlmodel import Session, select

from app.db import engine
from app.models import (
    ItemMaster,
    NodeMaster,
    InventoryByNode,
    ItemVelocityByNode,
    ReplenishmentSchedule,
    ShippingCostByNodeZone,
    WeatherRiskByNode,
)


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    with Session(engine) as session:
        print_section("ITEM MASTER")
        for row in session.exec(select(ItemMaster)).all():
            print(row)

        print_section("NODE MASTER")
        for row in session.exec(select(NodeMaster)).all():
            print(row)

        print_section("INVENTORY BY NODE")
        for row in session.exec(select(InventoryByNode)).all():
            print(row)

        print_section("ITEM VELOCITY BY NODE")
        for row in session.exec(select(ItemVelocityByNode)).all():
            print(row)

        print_section("REPLENISHMENT SCHEDULE")
        for row in session.exec(select(ReplenishmentSchedule)).all():
            print(row)

        print_section("SHIPPING COST BY NODE ZONE")
        for row in session.exec(select(ShippingCostByNodeZone)).all():
            print(row)

        print_section("WEATHER RISK BY NODE")
        for row in session.exec(select(WeatherRiskByNode)).all():
            print(row)


if __name__ == "__main__":
    main()