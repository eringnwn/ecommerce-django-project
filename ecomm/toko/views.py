from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone
from django.views import generic
from paypal.standard.forms import PayPalPaymentsForm


from .forms import CheckoutForm
from .models import ProdukItem, OrderProdukItem, Order, AlamatPengiriman, Payment

class KategoriListView(generic.ListView):
    def get(req, nama_kategori):
        if (nama_kategori == 'all'):
            nama = ''
            produk = ProdukItem.objects.all()
        else:
            nama = Kategori.objects.get(slug = nama_kategori)
            produk = ProductItem.objects.filter(kategori = nama)
        paginate_by = 4
        context = {
            'items' : produk
        }
        return render(self.req, 'home.html', context)

def hapus_produk(request, item_id):
    item = get_object_or_404(ProdukItem, id=item_id)
    item.delete()
    return redirect('toko:order-summary')

def HomeListView(req):
    # template_name = "home.html"
    produk = ProdukItem.objects.all()
    best = ProdukItem.objects.filter(label = 'BEST')
    new = ProdukItem.objects.filter(label = 'NEW')
    sale = ProdukItem.objects.filter(label = 'SALE')
    context = {
        'all' : produk,
        'best': best,
        'sale' : sale,
        'new' : new,
    }
    paginate_by = 4
    return render(req, "home.html", context)

class ProductDetailView(generic.DetailView):
    template_name = "product_detail.html"
    queryset = ProdukItem.objects.all()


class KontakView(generic.TemplateView):
    template_name = "kontak.html"


class CheckoutView(LoginRequiredMixin, generic.FormView):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if order.produk_items.count() == 0:
                messages.warning(
                    self.request,
                    "Belum ada belajaan yang Anda pesan, lanjutkan belanja",
                )
                return redirect("toko:home-produk-list")
        except ObjectDoesNotExist:
            order = {}
            messages.warning(
                self.request, "Belum ada belajaan yang Anda pesan, lanjutkan belanja"
            )
            return redirect("toko:home-produk-list")

        context = {
            "form": form,
            "keranjang": order,
        }
        template_name = "checkout.html"
        return render(self.request, template_name, context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                alamat_1 = form.cleaned_data.get("alamat_1")
                alamat_2 = form.cleaned_data.get("alamat_2")
                negara = form.cleaned_data.get("negara")
                kode_pos = form.cleaned_data.get("kode_pos")
                opsi_pembayaran = form.cleaned_data.get("opsi_pembayaran")
                alamat_pengiriman = AlamatPengiriman(
                    user=self.request.user,
                    alamat_1=alamat_1,
                    alamat_2=alamat_2,
                    negara=negara,
                    kode_pos=kode_pos,
                )

                alamat_pengiriman.save()
                order.alamat_pengiriman = alamat_pengiriman
                order.save()
                if opsi_pembayaran == "P":
                    return redirect("toko:payment", payment_method="paypal")
                else:
                    return redirect("toko:payment", payment_method="stripe")

            messages.warning(self.request, "Gagal checkout")
            return redirect("toko:checkout")
        except ObjectDoesNotExist:
            messages.error(self.request, "Tidak ada pesanan yang aktif")
            return redirect("toko:order-summary")


class PaymentView(LoginRequiredMixin, generic.FormView):
    def get(self, *args, **kwargs):
        template_name = "payment.html"
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)

            paypal_data = {
                "business": settings.PAYPAL_RECEIVER_EMAIL,
                "amount": order.get_total_harga_order,
                "item_name": f"Pembayaran belajanan order: {order.id}",
                "invoice": f"{order.id}-{timezone.now().timestamp()}",
                "currency_code": "USD",
                "notify_url": self.request.build_absolute_uri(reverse("paypal-ipn")),
                "return_url": self.request.build_absolute_uri(
                    reverse("toko:paypal-return")
                ),
                "cancel_return": self.request.build_absolute_uri(
                    reverse("toko:paypal-cancel")
                ),
            }

            qPath = self.request.get_full_path()
            isPaypal = "paypal" in qPath

            form = PayPalPaymentsForm(initial=paypal_data)
            context = {
                "paypalform": form,
                "order": order,
                "is_paypal": isPaypal,
            }
            return render(self.request, template_name, context)

        except ObjectDoesNotExist:
            return redirect("toko:checkout")


class OrderSummaryView(LoginRequiredMixin, generic.TemplateView):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {"keranjang": order}
            template_name = "order_summary.html"
            return render(self.request, template_name, context)
        except ObjectDoesNotExist:
            messages.error(self.request, "Tidak ada pesanan yang aktif")
            return redirect("/")

@login_required
def add_to_cart(request, slug):
    if request.user.is_authenticated:
        produk_item = get_object_or_404(ProdukItem, slug=slug)
        order_produk_item, _ = OrderProdukItem.objects.get_or_create(
            produk_item=produk_item, user=request.user, ordered=False
        )
        order_query = Order.objects.filter(user=request.user, ordered=False)
        if order_query.exists():
            order = order_query[0]
            if order.produk_items.filter(produk_item__slug=produk_item.slug).exists():
                order_produk_item.quantity += 1
                order_produk_item.save()
                pesan = (
                    f"ProdukItem sudah diupdate menjadi: { order_produk_item.quantity }"
                )
                messages.info(request, pesan)
                return redirect("toko:order-summary")
            else:
                order.produk_items.add(order_produk_item)
                messages.info(request, "ProdukItem pilihanmu sudah ditambahkan")
                return redirect("toko:order-summary")
        else:
            tanggal_order = timezone.now()
            order = Order.objects.create(user=request.user, tanggal_order=tanggal_order)
            order.produk_items.add(order_produk_item)
            messages.info(request, "ProdukItem pilihanmu sudah ditambahkan")
            return redirect("toko:order-summary")
    else:
        return redirect("/accounts/login")

@login_required
def remove_single_item_from_cart(request, slug):
    if request.user.is_authenticated:
        produk_item = get_object_or_404(ProdukItem, slug=slug)
        order_query = Order.objects.filter(user=request.user, ordered=False)
        if order_query.exists():
            order = order_query[0]
            if order.produk_items.filter(produk_item__slug=produk_item.slug).exists():
                try:
                    order_produk_item = OrderProdukItem.objects.filter(
                        produk_item=produk_item, user=request.user, ordered=False
                    ).first()  # Use first() instead of [0]

                    if order_produk_item.quantity > 1:
                        order_produk_item.quantity -= 1
                        order_produk_item.save()
                        pesan = f"ProdukItem sudah dikurangi. Jumlah saat ini: {order_produk_item.quantity}"
                    else:
                        order.produk_items.remove(order_produk_item)
                        pesan = "ProdukItem dihapus dari keranjang."

                    messages.info(request, pesan)
                    return redirect("toko:order-summary")
                except ObjectDoesNotExist:
                    order.produk_items.remove(order_produk_item)
                    print("Error: order ProdukItem sudah tidak ada")
            else:
                messages.info(request, "ProdukItem tidak ada")
                return redirect("toko:order-summary")
        else:
            messages.info(request, "ProdukItem tidak ada order yang aktif")
            return redirect("toko:order-summary", slug=slug)
    else:
        return redirect("/accounts/login")

@login_required
def remove_from_cart(request, slug):
    if request.user.is_authenticated:
        produk_item = get_object_or_404(ProdukItem, slug=slug)
        order_query = Order.objects.filter(user=request.user, ordered=False)
        if order_query.exists():
            order = order_query[0]
            if order.produk_items.filter(produk_item__slug=produk_item.slug).exists():
                try:
                    order_produk_item = OrderProdukItem.objects.filter(
                        produk_item=produk_item, user=request.user, ordered=False
                    ).first()  # Use first() instead of [0]

                    if order_produk_item.quantity > 1:
                        order_produk_item.quantity -= 1
                        order_produk_item.save()
                        pesan = f"ProdukItem sudah dikurangi. Jumlah saat ini: {order_produk_item.quantity}"
                    else:
                        order.produk_items.remove(order_produk_item)
                        pesan = "ProdukItem dihapus dari keranjang."

                    messages.info(request, pesan)
                    return redirect("toko:order-summary")
                except ObjectDoesNotExist:
                    order.produk_items.remove(order_produk_item)
                    print("Error: order ProdukItem sudah tidak ada")
            else:
                messages.info(request, "ProdukItem tidak ada")
                return redirect("toko:produk-detail", slug=slug)
        else:
            messages.info(request, "ProdukItem tidak ada order yang aktif")
            return redirect("toko:produk-detail", slug=slug)
    else:
        return redirect("/accounts/login")

# @csrf_exempt
def paypal_return(request):
    if request.user.is_authenticated:
        try:
            print("paypal return", request)
            order = Order.objects.get(user=request.user, ordered=False)
            payment = Payment()
            payment.user = request.user
            payment.amount = order.get_total_harga_order()
            payment.payment_option = "P"  # paypal kalai 'S' stripe
            payment.charge_id = f"{order.id}-{timezone.now()}"
            payment.timestamp = timezone.now()
            payment.save()

            order_produk_item = OrderProdukItem.objects.filter(
                user=request.user, ordered=False
            )
            order_produk_item.update(ordered=True)

            order.payment = payment
            order.ordered = True
            order.save()

            messages.info(request, "Pembayaran sudah diterima, terima kasih")
            return redirect("toko:home-produk-list")
        except ObjectDoesNotExist:
            messages.error(request, "Periksa kembali pesananmu")
            return redirect("toko:order-summary")
    else:
        return redirect("/accounts/login")


# @csrf_exempt
def paypal_cancel(request):
    messages.error(request, "Pembayaran dibatalkan")
    return redirect("toko:order-summary")
