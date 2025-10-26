from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
import requests
from datetime import datetime
import threading
import json
import os

class StockCard(BoxLayout):
    def __init__(self, name, ticker, price, change, change_percent, currency, on_delete, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 90
        self.padding = 15
        self.spacing = 10
        
        with self.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        info_box = BoxLayout(orientation='vertical', size_hint_x=0.55)
        name_label = Label(text=name, font_size='18sp', bold=True, color=(1, 1, 1, 1), halign='left')
        ticker_label = Label(text=ticker, font_size='14sp', color=(0.7, 0.7, 0.7, 1), halign='left')
        name_label.bind(size=name_label.setter('text_size'))
        ticker_label.bind(size=ticker_label.setter('text_size'))
        info_box.add_widget(name_label)
        info_box.add_widget(ticker_label)
        
        price_box = BoxLayout(orientation='vertical', size_hint_x=0.38)
        if currency == 'KRW':
            price_str = f'{int(price):,} KRW'
        else:
            price_str = f'${price:.2f}'
        price_label = Label(text=price_str, font_size='18sp', bold=True, color=(1, 1, 1, 1), halign='right')
        
        change_color = (0.9, 0.3, 0.3, 1) if change >= 0 else (0.3, 0.5, 0.9, 1)
        change_text = f'{change:+.2f} ({change_percent:+.2f}%)'
        change_label = Label(text=change_text, font_size='15sp', color=change_color, halign='right')
        
        price_label.bind(size=price_label.setter('text_size'))
        change_label.bind(size=change_label.setter('text_size'))
        price_box.add_widget(price_label)
        price_box.add_widget(change_label)
        
        delete_btn = Button(text='X', size_hint=(None, None), size=(50, 50), 
                          background_color=(0.8, 0.3, 0.3, 1), font_size='20sp')
        delete_btn.bind(on_press=lambda x: on_delete(ticker, name))
        
        self.add_widget(info_box)
        self.add_widget(price_box)
        self.add_widget(delete_btn)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class ExchangeCard(BoxLayout):
    def __init__(self, label, rate, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 70
        self.padding = 15
        
        with self.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        label_widget = Label(text=label, font_size='18sp', bold=True, color=(1, 1, 1, 1), halign='left')
        
        if 'KRW' in label:
            rate_text = f'{rate:,.2f} KRW'
        elif 'CNY' in label:
            rate_text = f'{rate:.4f} CNY'
        else:
            rate_text = f'{rate:.4f}'
        
        rate_widget = Label(text=rate_text, font_size='20sp', bold=True, color=(0.5, 0.8, 0.5, 1), halign='right')
        
        label_widget.bind(size=label_widget.setter('text_size'))
        rate_widget.bind(size=rate_widget.setter('text_size'))
        
        self.add_widget(label_widget)
        self.add_widget(rate_widget)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class AddStockPopup(Popup):
    def __init__(self, on_add, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Add Stock'
        self.size_hint = (0.8, 0.6)
        self.on_add = on_add
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        content.add_widget(Label(text='Select Market:', size_hint_y=None, height=30))
        
        market_box = BoxLayout(size_hint_y=None, height=50, spacing=5)
        self.kr_btn = Button(text='KR', background_color=(0.3, 0.5, 0.8, 1))
        self.us_btn = Button(text='US', background_color=(0.5, 0.5, 0.5, 1))
        self.cn_btn = Button(text='CN', background_color=(0.5, 0.5, 0.5, 1))
        
        self.kr_btn.bind(on_press=lambda x: self.select_market('KR'))
        self.us_btn.bind(on_press=lambda x: self.select_market('US'))
        self.cn_btn.bind(on_press=lambda x: self.select_market('CN'))
        
        market_box.add_widget(self.kr_btn)
        market_box.add_widget(self.us_btn)
        market_box.add_widget(self.cn_btn)
        content.add_widget(market_box)
        
        self.selected_market = 'KR'
        
        content.add_widget(Label(text='Ticker:', size_hint_y=None, height=30))
        self.ticker_input = TextInput(hint_text='005930', multiline=False, size_hint_y=None, height=40)
        content.add_widget(self.ticker_input)
        
        content.add_widget(Label(text='Name:', size_hint_y=None, height=30))
        self.name_input = TextInput(hint_text='Samsung', multiline=False, size_hint_y=None, height=40)
        content.add_widget(self.name_input)
        
        btn_box = BoxLayout(size_hint_y=None, height=50, spacing=10)
        add_btn = Button(text='Add', background_color=(0.3, 0.7, 0.3, 1))
        add_btn.bind(on_press=self.add_stock)
        cancel_btn = Button(text='Cancel', background_color=(0.7, 0.3, 0.3, 1))
        cancel_btn.bind(on_press=self.dismiss)
        btn_box.add_widget(add_btn)
        btn_box.add_widget(cancel_btn)
        content.add_widget(btn_box)
        
        self.content = content
    
    def select_market(self, market):
        self.selected_market = market
        self.kr_btn.background_color = (0.3, 0.5, 0.8, 1) if market == 'KR' else (0.5, 0.5, 0.5, 1)
        self.us_btn.background_color = (0.3, 0.5, 0.8, 1) if market == 'US' else (0.5, 0.5, 0.5, 1)
        self.cn_btn.background_color = (0.3, 0.5, 0.8, 1) if market == 'CN' else (0.5, 0.5, 0.5, 1)
    
    def add_stock(self, *args):
        ticker = self.ticker_input.text.strip()
        name = self.name_input.text.strip()
        
        if not ticker or not name:
            return
        
        if self.selected_market == 'KR':
            if not ticker.endswith('.KS') and not ticker.endswith('.KQ'):
                ticker = f"{ticker}.KS"
        elif self.selected_market == 'CN':
            if not ticker.endswith('.SS') and not ticker.endswith('.SZ'):
                ticker = f"{ticker}.SS"
        
        self.on_add(ticker, name, self.selected_market)
        self.dismiss()

class StockApp(App):
    def build(self):
        self.title = 'My Portfolio'
        self.stocks_file = 'my_stocks.json'
        self.load_stocks()
        
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        with main_layout.canvas.before:
            Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)
        main_layout.bind(pos=self.update_bg, size=self.update_bg)
        
        header = Label(text='My Portfolio', font_size='28sp', size_hint_y=None, height=60, bold=True, color=(1, 1, 1, 1))
        self.update_time_label = Label(text='Tap Refresh', font_size='12sp', size_hint_y=None, height=30, color=(0.7, 0.7, 0.7, 1))
        
        scroll = ScrollView(size_hint=(1, 1))
        self.content_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.content_layout.bind(minimum_height=self.content_layout.setter('height'))
        scroll.add_widget(self.content_layout)
        
        btn_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        add_btn = Button(text='+ Add', background_color=(0.3, 0.7, 0.3, 1), font_size='16sp')
        add_btn.bind(on_press=self.show_add_popup)
        
        refresh_btn = Button(text='Refresh', background_color=(0.3, 0.5, 0.8, 1), font_size='16sp')
        refresh_btn.bind(on_press=self.load_data)
        
        btn_row.add_widget(add_btn)
        btn_row.add_widget(refresh_btn)
        
        main_layout.add_widget(header)
        main_layout.add_widget(self.update_time_label)
        main_layout.add_widget(scroll)
        main_layout.add_widget(btn_row)
        
        return main_layout
    
    def update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def load_stocks(self):
        self.stocks = {
            'KR': [('005930.KS', 'Samsung'), ('000660.KS', 'SK Hynix')],
            'US': [('AAPL', 'Apple'), ('GOOGL', 'Google'), ('TSLA', 'Tesla')],
            'CN': []
        }
        
        if os.path.exists(self.stocks_file):
            try:
                with open(self.stocks_file, 'r', encoding='utf-8') as f:
                    self.stocks = json.load(f)
            except:
                pass
    
    def save_stocks(self):
        with open(self.stocks_file, 'w', encoding='utf-8') as f:
            json.dump(self.stocks, f, ensure_ascii=False)
    
    def show_add_popup(self, *args):
        popup = AddStockPopup(on_add=self.add_stock)
        popup.open()
    
    def add_stock(self, ticker, name, market):
        self.stocks[market].append((ticker, name))
        self.save_stocks()
        self.load_data()
    
    def delete_stock(self, ticker, name):
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        content.add_widget(Label(text=f'Delete {name}?', font_size='18sp'))
        
        btn_box = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        def confirm_delete(instance):
            for market in self.stocks:
                self.stocks[market] = [(t, n) for t, n in self.stocks[market] if t != ticker]
            self.save_stocks()
            self.load_data()
            popup.dismiss()
        
        yes_btn = Button(text='Delete', background_color=(0.8, 0.3, 0.3, 1))
        yes_btn.bind(on_press=confirm_delete)
        no_btn = Button(text='Cancel', background_color=(0.5, 0.5, 0.5, 1))
        no_btn.bind(on_press=lambda x: popup.dismiss())
        
        btn_box.add_widget(yes_btn)
        btn_box.add_widget(no_btn)
        content.add_widget(btn_box)
        
        popup = Popup(title='Confirm', content=content, size_hint=(0.8, 0.3))
        popup.open()
    
    def load_data(self, *args):
        self.update_time_label.text = 'Loading...'
        threading.Thread(target=self.fetch_data, daemon=True).start()
    
    def fetch_data(self):
        try:
            all_data = {'KR': [], 'US': [], 'CN': []}
            
            for market, stocks in self.stocks.items():
                for ticker, name in stocks:
                    data = self.get_stock_price(ticker, name)
                    if data:
                        all_data[market].append(data)
            
            usd_krw = self.get_exchange_rate("USD", "KRW")
            cny_krw = self.get_exchange_rate("CNY", "KRW")
            usd_cny = self.get_exchange_rate("USD", "CNY")
            
            Clock.schedule_once(lambda dt: self.update_ui(all_data, usd_krw, cny_krw, usd_cny))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)))
    
    def get_stock_price(self, ticker, name):
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if 'chart' not in data or not data['chart'].get('result'):
                return None
            
            result = data['chart']['result'][0]
            meta = result.get('meta', {})
            
            current_price = meta.get('regularMarketPrice')
            previous_close = meta.get('previousClose') or meta.get('chartPreviousClose')
            currency = meta.get('currency', 'USD')
            
            if current_price is None or previous_close is None:
                return None
            
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            return {
                'name': name,
                'ticker': ticker,
                'price': float(current_price),
                'change': float(change),
                'change_percent': float(change_percent),
                'currency': currency
            }
            
        except Exception as e:
            return None
    
    def get_exchange_rate(self, from_curr, to_curr):
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{from_curr}"
            response = requests.get(url, timeout=15)
            
            if response.status_code != 200:
                return 0
            
            data = response.json()
            return data['rates'].get(to_curr, 0)
        except:
            return 0
    
    def update_ui(self, all_data, usd_krw, cny_krw, usd_cny):
        self.content_layout.clear_widgets()
        
        if all_data['KR']:
            kr_title = Label(text='KR Stocks', font_size='22sp', size_hint_y=None, 
                            height=50, bold=True, color=(1, 1, 1, 1))
            self.content_layout.add_widget(kr_title)
            
            for stock in all_data['KR']:
                card = StockCard(
                    stock['name'], stock['ticker'], stock['price'],
                    stock['change'], stock['change_percent'], stock['currency'],
                    self.delete_stock
                )
                self.content_layout.add_widget(card)
        
        if all_data['US']:
            us_title = Label(text='US Stocks', font_size='22sp', size_hint_y=None, 
                            height=50, bold=True, color=(1, 1, 1, 1))
            self.content_layout.add_widget(us_title)
            
            for stock in all_data['US']:
                card = StockCard(
                    stock['name'], stock['ticker'], stock['price'],
                    stock['change'], stock['change_percent'], stock['currency'],
                    self.delete_stock
                )
                self.content_layout.add_widget(card)
        
        if all_data['CN']:
            cn_title = Label(text='CN Stocks', font_size='22sp', size_hint_y=None, 
                            height=50, bold=True, color=(1, 1, 1, 1))
            self.content_layout.add_widget(cn_title)
            
            for stock in all_data['CN']:
                card = StockCard(
                    stock['name'], stock['ticker'], stock['price'],
                    stock['change'], stock['change_percent'], stock['currency'],
                    self.delete_stock
                )
                self.content_layout.add_widget(card)
        
        ex_title = Label(text='Exchange', font_size='22sp', size_hint_y=None, 
                        height=50, bold=True, color=(1, 1, 1, 1))
        self.content_layout.add_widget(ex_title)
        
        if usd_krw:
            self.content_layout.add_widget(ExchangeCard('USD/KRW', usd_krw))
        if cny_krw:
            self.content_layout.add_widget(ExchangeCard('CNY/KRW', cny_krw))
        if usd_cny:
            self.content_layout.add_widget(ExchangeCard('USD/CNY', usd_cny))
        
        now = datetime.now().strftime('%H:%M:%S')
        self.update_time_label.text = f'Updated: {now}'
    
    def show_error(self, error):
        self.update_time_label.text = 'Error loading data'

if __name__ == '__main__':
    StockApp().run()
