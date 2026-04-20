from datetime import date, datetime, timezone

from sqlmodel import Session, delete

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


def seed_data() -> None:
    with Session(engine) as session:
        # Clear existing data
        session.exec(delete(WeatherRiskByNode))
        session.exec(delete(ShippingCostByNodeZone))
        session.exec(delete(ReplenishmentSchedule))
        session.exec(delete(ItemVelocityByNode))
        session.exec(delete(InventoryByNode))
        session.exec(delete(NodeMaster))
        session.exec(delete(ItemMaster))

        # Items
        items = [
            ItemMaster(
                item_id="SKU1001",
                item_name="Blue Jacket Large",
                category="Outerwear",
                original_retail_price=120.0,
                cogs=60.0,
                margin_percent=50.0,
                final_sale_flag=False,
            ),
            ItemMaster(
                item_id="SKU1002",
                item_name="Black Denim 32",
                category="Denim",
                original_retail_price=80.0,
                cogs=36.0,
                margin_percent=55.0,
                final_sale_flag=False,
            ),
            ItemMaster(
                item_id="SKU1003",
                item_name="White Sneakers 10",
                category="Footwear",
                original_retail_price=95.0,
                cogs=45.0,
                margin_percent=52.63,
                final_sale_flag=False,
            ),
        ]

        # Nodes
        nodes = [
            NodeMaster(
                node_id="STORE_A",
                node_type="STORE",
                city="Austin",
                state="TX",
                zip_code="78701",
                labor_cost_per_order=4.50,
                max_daily_capacity=150,
                current_capacity_utilization=110,
            ),
            NodeMaster(
                node_id="STORE_B",
                node_type="STORE",
                city="Dallas",
                state="TX",
                zip_code="75201",
                labor_cost_per_order=4.00,
                max_daily_capacity=160,
                current_capacity_utilization=70,
            ),
            NodeMaster(
                node_id="DC_1",
                node_type="DC",
                city="Fort Worth",
                state="TX",
                zip_code="76101",
                labor_cost_per_order=2.25,
                max_daily_capacity=2000,
                current_capacity_utilization=900,
            ),
        ]

        # Inventory
        inventory = [
            InventoryByNode(item_id="SKU1001", node_id="STORE_A", on_hand_qty=3, available_qty=2, protection_qty=1),
            InventoryByNode(item_id="SKU1002", node_id="STORE_A", on_hand_qty=4, available_qty=3, protection_qty=1),
            InventoryByNode(item_id="SKU1003", node_id="STORE_A", on_hand_qty=2, available_qty=1, protection_qty=1),

            InventoryByNode(item_id="SKU1001", node_id="STORE_B", on_hand_qty=20, available_qty=18, protection_qty=2),
            InventoryByNode(item_id="SKU1002", node_id="STORE_B", on_hand_qty=12, available_qty=10, protection_qty=2),
            InventoryByNode(item_id="SKU1003", node_id="STORE_B", on_hand_qty=8, available_qty=7, protection_qty=1),

            InventoryByNode(item_id="SKU1001", node_id="DC_1", on_hand_qty=500, available_qty=480, protection_qty=0),
            InventoryByNode(item_id="SKU1002", node_id="DC_1", on_hand_qty=350, available_qty=330, protection_qty=0),
            InventoryByNode(item_id="SKU1003", node_id="DC_1", on_hand_qty=250, available_qty=245, protection_qty=0),
        ]

        # Velocity
        velocities = [
            ItemVelocityByNode(item_id="SKU1001", node_id="STORE_A", weekly_velocity=9.0, seasonality_factor=1.2),
            ItemVelocityByNode(item_id="SKU1002", node_id="STORE_A", weekly_velocity=7.5, seasonality_factor=1.1),
            ItemVelocityByNode(item_id="SKU1003", node_id="STORE_A", weekly_velocity=6.0, seasonality_factor=1.0),

            ItemVelocityByNode(item_id="SKU1001", node_id="STORE_B", weekly_velocity=3.0, seasonality_factor=1.0),
            ItemVelocityByNode(item_id="SKU1002", node_id="STORE_B", weekly_velocity=4.0, seasonality_factor=1.0),
            ItemVelocityByNode(item_id="SKU1003", node_id="STORE_B", weekly_velocity=2.5, seasonality_factor=1.0),

            ItemVelocityByNode(item_id="SKU1001", node_id="DC_1", weekly_velocity=20.0, seasonality_factor=1.0),
            ItemVelocityByNode(item_id="SKU1002", node_id="DC_1", weekly_velocity=18.0, seasonality_factor=1.0),
            ItemVelocityByNode(item_id="SKU1003", node_id="DC_1", weekly_velocity=15.0, seasonality_factor=1.0),
        ]

        # Replenishment
        replenishments = [
            ReplenishmentSchedule(item_id="SKU1001", node_id="STORE_A", next_arrival_date=date(2026, 4, 24), frequency_days=7),
            ReplenishmentSchedule(item_id="SKU1002", node_id="STORE_A", next_arrival_date=date(2026, 4, 25), frequency_days=7),
            ReplenishmentSchedule(item_id="SKU1003", node_id="STORE_A", next_arrival_date=date(2026, 4, 26), frequency_days=7),

            ReplenishmentSchedule(item_id="SKU1001", node_id="STORE_B", next_arrival_date=date(2026, 4, 20), frequency_days=4),
            ReplenishmentSchedule(item_id="SKU1002", node_id="STORE_B", next_arrival_date=date(2026, 4, 20), frequency_days=4),
            ReplenishmentSchedule(item_id="SKU1003", node_id="STORE_B", next_arrival_date=date(2026, 4, 21), frequency_days=4),

            ReplenishmentSchedule(item_id="SKU1001", node_id="DC_1", next_arrival_date=date(2026, 4, 19), frequency_days=2),
            ReplenishmentSchedule(item_id="SKU1002", node_id="DC_1", next_arrival_date=date(2026, 4, 19), frequency_days=2),
            ReplenishmentSchedule(item_id="SKU1003", node_id="DC_1", next_arrival_date=date(2026, 4, 19), frequency_days=2),
        ]

        # Shipping cost by zone
        shipping_costs = [
            ShippingCostByNodeZone(node_id="STORE_A", destination_zone="TX_LOCAL", service_level="Ground", shipping_cost=8.50, est_transit_days=1),
            ShippingCostByNodeZone(node_id="STORE_B", destination_zone="TX_LOCAL", service_level="Ground", shipping_cost=9.25, est_transit_days=2),
            ShippingCostByNodeZone(node_id="DC_1", destination_zone="TX_LOCAL", service_level="Ground", shipping_cost=11.00, est_transit_days=2),

            ShippingCostByNodeZone(node_id="STORE_A", destination_zone="TX_LOCAL", service_level="Express", shipping_cost=14.50, est_transit_days=1),
            ShippingCostByNodeZone(node_id="STORE_B", destination_zone="TX_LOCAL", service_level="Express", shipping_cost=15.25, est_transit_days=1),
            ShippingCostByNodeZone(node_id="DC_1", destination_zone="TX_LOCAL", service_level="Express", shipping_cost=17.00, est_transit_days=1),
        ]

        # Weather
        weather = [
            WeatherRiskByNode(
                node_id="STORE_A",
                weather_risk_score=0.30,
                weather_note="Light storm risk",
                last_updated=datetime.now(timezone.utc),
            ),
            WeatherRiskByNode(
                node_id="STORE_B",
                weather_risk_score=0.10,
                weather_note="Clear",
                last_updated=datetime.now(timezone.utc),
            ),
            WeatherRiskByNode(
                node_id="DC_1",
                weather_risk_score=0.05,
                weather_note="Clear",
                last_updated=datetime.now(timezone.utc),
            ),
        ]

        for row in items + nodes + inventory + velocities + replenishments + shipping_costs + weather:
            session.add(row)

        session.commit()


if __name__ == "__main__":
    seed_data()
    print("Seed data inserted successfully.")