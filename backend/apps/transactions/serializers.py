from decimal import Decimal
from rest_framework import serializers
from .models import Transaction, Category, Person, ExpenseSplit


class ExpenseSplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseSplit
        fields = ['id', 'person', 'person_name_snapshot', 'amount', 'paid_back', 'paid_back_at', 'note', 'created_at']
        read_only_fields = ['id', 'created_at', 'person_name_snapshot']


class TransactionListSerializer(serializers.ModelSerializer):
    net_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    split_count = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'date', 'amount', 'net_amount', 'merchant', 'type',
            'description', 'category_name', 'category', 'split_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'date', 'amount', 'merchant', 'type', 'net_amount', 'split_count', 'created_at', 'updated_at']

    def get_split_count(self, obj):
        return obj.splits.count()


class TransactionDetailSerializer(TransactionListSerializer):
    splits = ExpenseSplitSerializer(many=True, read_only=True)

    class Meta(TransactionListSerializer.Meta):
        fields = TransactionListSerializer.Meta.fields + ['splits']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'label', 'is_default', 'owner', 'created_at']
        read_only_fields = ['id', 'name', 'is_default', 'owner', 'created_at']


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['id', 'name', 'archived', 'created_at']
        read_only_fields = ['id', 'created_at']
