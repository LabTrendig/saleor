import graphene
from graphene import relay

from ...core.permissions import DiscountPermissions
from ...discount import models
from ..channel.types import ChannelContext, ChannelContextType
from ..core import types
from ..core.connection import CountableDjangoObjectType
from ..core.fields import PrefetchingConnectionField
from ..core.types import Money
from ..decorators import permission_required
from ..product.types import Category, Collection, Product
from ..translations.fields import TranslationField
from ..translations.types import SaleTranslation, VoucherTranslation
from .enums import DiscountValueTypeEnum, VoucherTypeEnum


class Sale(CountableDjangoObjectType):
    categories = PrefetchingConnectionField(
        Category, description="List of categories this sale applies to."
    )
    collections = PrefetchingConnectionField(
        Collection, description="List of collections this sale applies to."
    )
    products = PrefetchingConnectionField(
        Product, description="List of products this sale applies to."
    )
    translation = TranslationField(SaleTranslation, type_name="sale")

    class Meta:
        description = (
            "Sales allow creating discounts for categories, collections or products "
            "and are visible to all the customers."
        )
        interfaces = [relay.Node]
        model = models.Sale
        only_fields = ["end_date", "id", "name", "start_date", "type", "value"]

    @staticmethod
    def resolve_categories(root: models.Sale, *_args, **_kwargs):
        return root.categories.all()

    @staticmethod
    def resolve_collections(root: models.Sale, info, **_kwargs):
        return root.collections.visible_to_user(info.context.user)

    @staticmethod
    def resolve_products(root: models.Sale, info, **_kwargs):
        return root.products.visible_to_user(info.context.user)


class VoucherChannelListing(CountableDjangoObjectType):
    class Meta:
        description = "Represents voucher channel listing."
        model = models.VoucherChannelListing
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "channel", "discount_value", "currency", "min_spent"]

    @staticmethod
    def resolve_channel(root: models.VoucherChannelListing, _info, **_kwargs):
        # TODO: Add dataloader.
        return root.channel


class Voucher(ChannelContextType, CountableDjangoObjectType):
    categories = PrefetchingConnectionField(
        Category, description="List of categories this voucher applies to."
    )
    collections = PrefetchingConnectionField(
        Collection, description="List of collections this voucher applies to."
    )
    products = PrefetchingConnectionField(
        Product, description="List of products this voucher applies to."
    )
    countries = graphene.List(
        types.CountryDisplay,
        description="List of countries available for the shipping voucher.",
    )
    translation = TranslationField(VoucherTranslation, type_name="voucher")
    discount_value_type = DiscountValueTypeEnum(
        description="Determines a type of discount for voucher - value or percentage",
        required=True,
    )
    discount_value = graphene.Float(description="Voucher value.")
    currency = graphene.String(description="Currency code for voucher.")
    min_spent = graphene.Field(
        Money, description="Minimum order value to apply voucher."
    )
    type = VoucherTypeEnum(description="Determines a type of voucher.", required=True)
    channel_listing = graphene.List(
        graphene.NonNull(VoucherChannelListing),
        description="List of availability in channels for the voucher.",
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = (
            "Vouchers allow giving discounts to particular customers on categories, "
            "collections or specific products. They can be used during checkout by "
            "providing valid voucher codes."
        )
        only_fields = [
            "apply_once_per_order",
            "apply_once_per_customer",
            "code",
            "discount_value_type",
            "end_date",
            "id",
            "min_checkout_items_quantity",
            "name",
            "start_date",
            "type",
            "usage_limit",
            "used",
        ]
        interfaces = [relay.Node]
        model = models.Voucher

    @staticmethod
    def resolve_categories(root: ChannelContext[models.Voucher], *_args, **_kwargs):
        return root.node.categories.all()

    @staticmethod
    def resolve_collections(root: ChannelContext[models.Voucher], info, **_kwargs):
        return root.node.collections.visible_to_user(info.context.user)

    @staticmethod
    def resolve_products(root: ChannelContext[models.Voucher], info, **_kwargs):
        return root.node.products.visible_to_user(info.context.user)

    @staticmethod
    def resolve_countries(root: ChannelContext[models.Voucher], *_args, **_kwargs):
        return [
            types.CountryDisplay(code=country.code, country=country.name)
            for country in root.node.countries
        ]

    @staticmethod
    def resolve_discount_value(root: ChannelContext[models.Voucher], *_args, **_kwargs):
        channel_listing = root.node.channel_listing.filter(
            channel__slug=str(root.channel_slug)
        ).first()
        return channel_listing.discount_value if channel_listing else None

    @staticmethod
    def resolve_currency(root: ChannelContext[models.Voucher], *_args, **_kwargs):
        channel_listing = root.node.channel_listing.filter(
            channel__slug=str(root.channel_slug)
        ).first()
        return channel_listing.currency if channel_listing else None

    @staticmethod
    def resolve_min_spent(root: ChannelContext[models.Voucher], *_args, **_kwargs):
        channel_listing = root.node.channel_listing.filter(
            channel__slug=str(root.channel_slug)
        ).first()
        return channel_listing.min_spent if channel_listing else None

    @staticmethod
    @permission_required(DiscountPermissions.MANAGE_DISCOUNTS)
    def resolve_channel_listing(root: ChannelContext[models.Voucher], _info, **_kwargs):
        # TODO: Add dataloader.
        return root.node.channel_listing.all()
