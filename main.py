"""
CLI interactivo del agente Santander.
Ejecutar: python main.py
"""

import sys
from config import Config
from agent import SalesAgent

BANNER = """
╔══════════════════════════════════════════════════╗
║     Santander Function Calling LLM — GPT-4o      ║
║  Pregunta sobre colocaciones, canales o líderes  ║
║  Escribe 'salir' para terminar                   ║
╚══════════════════════════════════════════════════╝

Ejemplos:
  • ¿Cuántos créditos se colocaron este mes?
  • ¿Qué canal tuvo mayor monto en marzo 2026?
  • ¿Cómo está el ranking de líderes?
  • ¿Cuál es el monto promedio por crédito?
"""


def main():
    try:
        config = Config.from_env()
    except KeyError as e:
        print(f"Error: falta la variable de entorno {e}")
        print("Copia .env.example a .env y completa los valores.")
        sys.exit(1)

    print(BANNER)
    agent = SalesAgent(config)

    while True:
        try:
            user_input = input("Tú: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nHasta luego.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("salir", "exit", "quit"):
            print("Hasta luego.")
            break

        print("\nAgente: ", end="", flush=True)
        reply = agent.chat(user_input)
        print(reply)
        print()


if __name__ == "__main__":
    main()
