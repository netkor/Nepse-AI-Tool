# Generated migration to add the Phase 8 signal history tables.

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0001_initial'),
        ('signals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SignalHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('signal_id', models.UUIDField(db_index=True, default=uuid.uuid4, unique=True)),
                ('signal_type', models.CharField(choices=[('rsi', 'RSI'), ('macd', 'MACD'), ('breakout', 'Breakout'), ('volume_spike', 'Volume Spike')], db_index=True, max_length=20)),
                ('direction', models.CharField(choices=[('buy', 'Buy'), ('sell', 'Sell'), ('neutral', 'Neutral')], db_index=True, max_length=10)),
                ('price', models.DecimalField(decimal_places=2, db_index=True, max_digits=15)),
                ('strength', models.FloatField(help_text='Signal confidence/strength (0.0-1.0)')),
                ('message', models.TextField(help_text='Human-readable signal description')),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('indicators', models.JSONField(blank=True, default=dict, help_text='Raw indicator values used for signal generation')),
                ('signal_generation_time', models.DateTimeField(auto_now_add=True, db_index=True, help_text='When this signal was generated')),
                ('high_price_post_signal', models.DecimalField(blank=True, decimal_places=2, help_text='Highest price after signal', max_digits=15, null=True)),
                ('low_price_post_signal', models.DecimalField(blank=True, decimal_places=2, help_text='Lowest price after signal', max_digits=15, null=True)),
                ('profit_loss_percent', models.FloatField(blank=True, help_text='Profit/loss if sold at low_price_post_signal', null=True)),
                ('roi_percent', models.FloatField(blank=True, help_text='Return on investment percentage', null=True)),
                ('users_notified', models.JSONField(blank=True, default=list, help_text='User IDs who were notified of this signal')),
                ('notifications_sent', models.IntegerField(default=0)),
                ('was_profitable', models.BooleanField(blank=True, help_text='True if signal resulted in profit', null=True)),
                ('was_actionable', models.BooleanField(default=True, help_text='Whether the signal was strong enough to act on')),
                ('stock', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='signal_histories', to='stocks.stock')),
                ('alert', models.ForeignKey(blank=True, help_text='Associated alert if this signal triggered an alert', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signal_histories', to='alerts.pricealert')),
            ],
            options={
                'db_table': 'signals_history',
                'ordering': ['-signal_generation_time'],
                'indexes': [models.Index(fields=['stock', 'signal_type', 'signal_generation_time'], name='signals_hi_stock_i_2bb52c_idx'), models.Index(fields=['direction', 'signal_generation_time'], name='signals_hi_direct_2bdc93_idx'), models.Index(fields=['strength', 'signal_generation_time'], name='signals_hi_streng_0ed3d1_idx')],
            },
        ),
        migrations.CreateModel(
            name='SignalPerformance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('signal_type', models.CharField(choices=[('rsi', 'RSI'), ('macd', 'MACD'), ('breakout', 'Breakout'), ('volume_spike', 'Volume Spike')], db_index=True, max_length=20)),
                ('direction', models.CharField(choices=[('buy', 'Buy'), ('sell', 'Sell'), ('all', 'All')], max_length=10)),
                ('period', models.CharField(choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('all_time', 'All Time')], db_index=True, max_length=20)),
                ('period_start', models.DateTimeField(db_index=True)),
                ('period_end', models.DateTimeField(blank=True, null=True)),
                ('total_signals', models.IntegerField(default=0)),
                ('profitable_signals', models.IntegerField(default=0)),
                ('avg_strength', models.FloatField(default=0.0)),
                ('avg_roi', models.FloatField(default=0.0)),
                ('win_rate', models.FloatField(default=0.0, help_text='Percentage of profitable signals')),
                ('total_pnl', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('best_trade', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('worst_trade', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('drawdown', models.FloatField(default=0.0, help_text='Maximum drawdown %')),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'signals_performance',
                'ordering': ['-period_start'],
                'unique_together': {('signal_type', 'direction', 'period', 'period_start')},
                'indexes': [models.Index(fields=['signal_type', 'period'], name='signals_pe_signal_1f4d6f_idx'), models.Index(fields=['period_start', 'period_end'], name='signals_pe_period_99c1f4_idx')],
            },
        ),
    ]
