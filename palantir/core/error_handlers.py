def register_error_handlers(app):
    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc):
        return {"error": str(exc)}
