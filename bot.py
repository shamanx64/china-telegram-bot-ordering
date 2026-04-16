import logging
import os
from dataclasses import dataclass

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Dish:
    key: str
    name: str
    price: float


MENU = [
    Dish("pizza", "Pepperoni Pizza", 12.50),
    Dish("burger", "Classic Burger", 8.90),
    Dish("pasta", "Creamy Pasta", 10.20),
    Dish("salad", "Caesar Salad", 7.40),
    Dish("soup", "Tomato Soup", 5.60),
    Dish("cake", "Chocolate Cake", 6.30),
]

MENU_BY_KEY = {dish.key: dish for dish in MENU}


def get_cart(context: ContextTypes.DEFAULT_TYPE) -> dict[str, int]:
    return context.user_data.setdefault("cart", {})


def money(amount: float) -> str:
    return f"${amount:.2f}"


def build_menu_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"{dish.name} - {money(dish.price)}", callback_data=f"add:{dish.key}")]
        for dish in MENU
    ]
    rows.append(
        [
            InlineKeyboardButton("View cart", callback_data="cart"),
            InlineKeyboardButton("Checkout", callback_data="checkout"),
        ]
    )
    rows.append([InlineKeyboardButton("Clear order", callback_data="clear")])
    return InlineKeyboardMarkup(rows)


def build_cart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Add more items", callback_data="menu"),
                InlineKeyboardButton("Checkout", callback_data="checkout"),
            ],
            [InlineKeyboardButton("Clear order", callback_data="clear")],
        ]
    )


def format_menu_text() -> str:
    lines = ["Today's menu:", ""]
    for dish in MENU:
        lines.append(f"• {dish.name} — {money(dish.price)}")
    lines.append("")
    lines.append("Tap a dish to add it to your order.")
    return "\n".join(lines)


def format_cart(cart: dict[str, int]) -> str:
    if not cart:
        return "Your cart is empty. Choose dishes from the menu to start an order."

    lines = ["Your current order:", ""]
    total = 0.0

    for dish_key, quantity in cart.items():
        dish = MENU_BY_KEY[dish_key]
        line_total = dish.price * quantity
        total += line_total
        lines.append(f"• {dish.name} x{quantity} — {money(line_total)}")

    lines.append("")
    lines.append(f"Total so far: {money(total)}")
    return "\n".join(lines)


def format_receipt(cart: dict[str, int]) -> str:
    lines = ["Receipt", "--------------------"]
    total = 0.0

    for dish_key, quantity in cart.items():
        dish = MENU_BY_KEY[dish_key]
        line_total = dish.price * quantity
        total += line_total
        lines.append(f"{dish.name} x{quantity} = {money(line_total)}")

    lines.append("--------------------")
    lines.append(f"Total: {money(total)}")
    lines.append("")
    lines.append("Thank you for your order!")
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    get_cart(context)
    text = (
        "Welcome to the food ordering bot.\n\n"
        "You can browse the menu, add multiple dishes, and receive an instant receipt."
    )
    await update.message.reply_text(text)
    await update.message.reply_text(format_menu_text(), reply_markup=build_menu_keyboard())


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(format_menu_text(), reply_markup=build_menu_keyboard())


async def cart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cart = get_cart(context)
    await update.message.reply_text(format_cart(cart), reply_markup=build_cart_keyboard())


async def checkout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cart = get_cart(context)
    if not cart:
        await update.message.reply_text(
            "Your cart is empty, so there is nothing to checkout yet.",
            reply_markup=build_menu_keyboard(),
        )
        return

    receipt = format_receipt(cart)
    context.user_data["cart"] = {}
    await update.message.reply_text(receipt)
    await update.message.reply_text(
        "If you'd like another order, the menu is ready below.",
        reply_markup=build_menu_keyboard(),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    cart = get_cart(context)
    action = query.data

    if action == "menu":
        await query.edit_message_text(format_menu_text(), reply_markup=build_menu_keyboard())
        return

    if action == "cart":
        await query.edit_message_text(format_cart(cart), reply_markup=build_cart_keyboard())
        return

    if action == "clear":
        context.user_data["cart"] = {}
        await query.edit_message_text(
            "Your order has been cleared.\n\nChoose dishes to start again.",
            reply_markup=build_menu_keyboard(),
        )
        return

    if action == "checkout":
        if not cart:
            await query.edit_message_text(
                "Your cart is empty. Add at least one dish before checkout.",
                reply_markup=build_menu_keyboard(),
            )
            return

        receipt = format_receipt(cart)
        context.user_data["cart"] = {}
        await query.edit_message_text(receipt)
        await query.message.reply_text(
            "You can start a new order anytime from the menu below.",
            reply_markup=build_menu_keyboard(),
        )
        return

    if action.startswith("add:"):
        dish_key = action.split(":", maxsplit=1)[1]
        dish = MENU_BY_KEY.get(dish_key)
        if dish is None:
            await query.message.reply_text("That dish is no longer available.")
            return

        cart[dish_key] = cart.get(dish_key, 0) + 1
        quantity = cart[dish_key]
        await query.message.reply_text(
            f"Added {dish.name} to your order. Quantity: {quantity}\n"
            f"Current total: {money(sum(MENU_BY_KEY[key].price * qty for key, qty in cart.items()))}"
        )
        await query.edit_message_text(format_menu_text(), reply_markup=build_menu_keyboard())


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set the TELEGRAM_BOT_TOKEN environment variable before starting the bot.")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("cart", cart_command))
    application.add_handler(CommandHandler("checkout", checkout_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot is starting")
    application.run_polling()


if __name__ == "__main__":
    main()
