from asyncio import run

from flat.parser import main, get_xlsx, form_data

def start_dev():
    error_mass = []
    run(main(error_mass=error_mass))
    format_data: list[dict] = form_data()
    get_xlsx(format_data)