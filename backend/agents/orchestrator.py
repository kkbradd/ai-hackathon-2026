import asyncio
import random

from agents.operational_agent import run_operational_agent
from agents.shipment_agent import run_shipment_agent
from agents.inventory_agent import run_inventory_agent
from agents.customer_issue_agent import run_customer_issue_agent


def _run_simulation_tick():
    from database import SessionLocal
    import simulation as sim
    db = SessionLocal()
    try:
        sim._generate_new_order(db)
        if random.random() < 0.10:
            sim._maybe_generate_complaint(db)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Agent:simulation_tick] Hata: {e}")
    finally:
        db.close()


class AgentOrchestrator:
    # (name, interval_seconds, fn, startup_delay_seconds)
    # Stagger LLM agents so they don't all fire simultaneously on boot.
    # simulation_tick has no LLM so it runs immediately (delay=0).
    SCHEDULE = [
        ("simulation_tick", 120,  _run_simulation_tick, 0),
        ("shipment",        600,  run_shipment_agent,   60),
        ("operational",     900,  run_operational_agent, 120),
        ("inventory",       1800, run_inventory_agent,  180),
        ("customer_issue",  1800, run_customer_issue_agent, 240),
    ]

    def __init__(self):
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        for name, interval, fn, delay in self.SCHEDULE:
            task = asyncio.create_task(self._agent_loop(name, interval, fn, delay))
            self._tasks.append(task)

    async def _agent_loop(self, name: str, interval: int, fn, startup_delay: int):
        print(f"[Agent:{name}] Başlatıldı — interval {interval}s, ilk çalışma {startup_delay}s sonra")
        if startup_delay > 0:
            await asyncio.sleep(startup_delay)
        try:
            await asyncio.to_thread(fn)
            print(f"[Agent:{name}] Başlangıç çalışması tamamlandı.")
        except Exception as e:
            print(f"[Agent:{name}] Başlangıç hatası: {e}")
        while True:
            await asyncio.sleep(interval)
            try:
                await asyncio.to_thread(fn)
            except Exception as e:
                print(f"[Agent:{name}] Döngü hatası: {e}")

    async def stop(self):
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        print("[AgentOrchestrator] Tüm ajanlar durduruldu.")
