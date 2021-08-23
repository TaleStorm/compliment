from bot_config.bot_messages import RedisMiddleware, dp, executor, on_startup

if __name__ == '__main__':
    dp.middleware.setup(RedisMiddleware())
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
