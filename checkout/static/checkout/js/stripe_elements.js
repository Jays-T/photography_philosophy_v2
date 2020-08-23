/* Core of the code here was taken from
https://stripe.com/docs/payments/accept-a-payment

With elements adapted from Code Institute Boutique Ado Project

CSS from:
https://stripe.com/docs/stripe-js
*/

var stripePublicKey = $("#id_stripe_public_key").text().slice(1, -1);
var clientSecret = $("#id_client_secret").text().slice(1, -1);
var stripe = Stripe(stripePublicKey);
var elements = stripe.elements();
var style = {
  base: {
    color: "#000",
    fontFamily: "Arial, sans-serif",
    fontSmoothing: "antialiased",
    fontSize: "16px",
    "::placeholder": {
      color: "#32325d",
    },
  },
  invalid: {
    fontFamily: "Arial, sans-serif",
    color: "#fa755a",
    /*dc3545*/
    iconColor: "#fa755a",
  },
};
var card = elements.create("card", { style: style });
card.mount("#card-element");

// Handle validation errors
const errorDiv = document.getElementById("card-errors");

card.addEventListener("change", function (event) {
  if (event.error) {
    var html = `
            <span class="icon" role="alert">
                <i class="fas fa-times"></i>
            </span>
            <span>${event.error.message}</span>
        `;
    $(errorDiv).html(html);
  } else {
    errorDiv.textContent = "";
  }
});

// Handle form submission (adapted from stripe documentation)

let form = document.getElementById("payment-form");

form.addEventListener("submit", function (ev) {
  // On submit prevent form submission
  ev.preventDefault();
  card.update({ disabled: true });
  $("#submit-button").attr("disabled", true);
  $("#payment-form").fadeToggle(100);

  // Capture form data
  var saveInfo = Boolean($("#id-save-info").attr("checked"));
  var csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
  var postData = {
    csrfmiddlewaretoken: csrfToken,
    client_secret: clientSecret,
    save_info: saveInfo,
  };
  var url = "/checkout/checkout_data_cache/";

  // Post data to checkout_data_cache view 
  $.post(url, postData)
    .done(function () {
      // On 200 response call stripe confirm card payment method
      stripe.confirmCardPayment(clientSecret, {
          payment_method: {
            card: card,
            billing_details: {
              name: $.trim(form.full_name.value),
              phone: $.trim(form.phone_number.value),
              email: $.trim(form.email.value),
              address: {
                line1: $.trim(form.street_address1.value),
                line2: $.trim(form.street_address2.value),
                city: $.trim(form.town_or_city.value),
                country: $.trim(form.country.value),
                state: $.trim(form.county.value),
              },
            },
          },
          shipping: {
            name: $.trim(form.full_name.value),
            phone: $.trim(form.phone_number.value),
            address: {
              line1: $.trim(form.street_address1.value),
              line2: $.trim(form.street_address2.value),
              city: $.trim(form.town_or_city.value),
              country: $.trim(form.country.value),
              postal_code: $.trim(form.postcode.value),
              state: $.trim(form.county.value),
            },
          },
        }).then(function (result) {
          if (result.error) {
            // If error in form display error message and return user to form 
            var html = `
            <span class="icon" role="alert">
                <i class="fas fa-times"></i>
            </span>
            <span>${result.error.message}</span>
        `;
            $(errorDiv).html(html);
            $("#payment-form").fadeToggle(100);
            card.update({ disabled: false });
            $("#submit-button").attr("disabled", false);
          } else {
            // If all is successful submit the form data with payment intent to stripe
            if (result.paymentIntent.status === "succeeded") {
              form.submit();
            }
          }
        });
    }).fail(function () {
      // If data not posted to view correctly reload page with error message,
      // User not charged and order not processed
      location.reload();
    });
});
