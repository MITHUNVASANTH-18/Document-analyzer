import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import base64
import os
from mimetypes import guess_type
import json
import re
from dotenv import load_dotenv
import requests
import streamlit.components.v1 as components

load_dotenv()
genai.configure(api_key='')
# model = genai.GenerativeModel("gemini-1.5-flash")

st.title("📄 Document Analyzer")


model = genai.GenerativeModel("gemini-2.5-pro-preview-05-06")


default_prompt = """
Analyze the given document. First, detect the source language of the document. If it is not in English, then translate it into English before proceeding.

Then, deeply analyze the content — ultra-deep, ultra-important, ultra-analyze — and extract the useful features in the given format. If you can't find any value for a field, just put "NA" or "not assigned", but make the output as reliable as possible. Reliability is a key factor here — very important.

⚠️ Strictly return the output ONLY as a raw JSON object that matches the following schema. Do not wrap it in markdown or provide any extra explanation.
1. `chain_of_ownership`: Clearly determine the history of ownership of the property — names and transitions.
2. cost_evaluation: Extract and analyze pricing details.

- If available, extract the **consideration price** and compare it with the **guideline value**.
- Calculate the **difference** (Above, Below, or Equal).
- Extract and validate the **stamp duty** amount paid. If the stamp duty rate is given (e.g. 4%), verify if the paid amount matches the expected value.
- Conclude with clear **remarks** on whether the valuation and stamp duty appear fair, inflated, or inconsistent.

⚠️ Return the `cost_evaluation` as a JSON object exactly like the following format:
3. Property Location Details Extraction
Carefully extract and validate all property location information from the document. Ensure the following:

Property address: Full address including property number, street, area, village, taluk, district, state, and pin code.

Khasra/Survey/Plot numbers: As mentioned.

Boundary description: Extract what's mentioned on all four sides — North, South, East, West.

Latitude/Longitude: If explicitly mentioned in the document, extract directly. If not mentioned, infer from the full address if possible.

Consistency Check: Confirm that these details are consistent across the deed (especially pages like e-Stamp, registration certificate, and property description).


4.Signature Verification & Signing Surface Analysis
  Carefully analyze each page of the document to:

  Identify inconsistencies, forgeries, or variations in signatures (e.g., spelling differences, different styles, scanned signs).

  Verify the surface on which signatures were made:

  Was the page a plain white paper, with text possibly handwritten or typed after printing?

  Was it a pre-printed official/stamp/legal paper?

  Was the signature likely scanned, copied, or digitally inserted?

  Provide:

  status: "Match", "Mismatch Detected", or "Forgery Suspected"

  pages_with_signatures: List of page numbers containing signatures

  signatures_mismatched: List any name variations or irregularities (e.g., "Page 5: 'Anju Khanam' vs Page 2: 'Anju Khurana'")

  signed_on: Specify surface type per page or general (e.g., "plain_white_paper", "printed_legal_paper", "e-stamp_paper")

  signed_properly: Indicate if the signatures appear to have been done after the page was printed

  notes: Add relevant remarks about signature authenticity or unusual findings (e.g., "Signature looks scanned on Page 4", "Photo mismatch on e-Stamp")
5. `signed_properly`: Flag if the document is signed on plain white paper or appears to have been signed after printing.

type PropertyDeed = {
  property_deed?: {
    document_id?: string;
    deed_type?: string;
    registration_details?: {
      registration_number?: string;
      registration_date?: string;
      sub_registrar_office?: string;
      registration_district?: string;
    };
    parties?: {
      seller?: {
        name?: string;
        address?: string;
        pan?: string;
        aadhaar?: string;
      };
      buyer?: {
        name?: string;
        address?: string;
        pan?: string;
        aadhaar?: string;
      };
      power_of_attorney?: {
        is_applicable?: boolean;
        details?: any | null;
      };
    };
    property_details?: {
      survey_number?: string;
      plot_number?: string;
      door_number?: string;
      extent?: {
        land_area_sqft?: number;
        builtup_area_sqft?: number;
      };
      property_address?: string;
      village?: string;
      taluk?: string;
      district?: string;
      state?: string;
      pin_code?: string;
      boundary_description?: {
        north?: string;
        south?: string;
        east?: string;
        west?: string;
      };
    };
    legal_info?: {
      ownership_type?: string;
      land_use_type?: string;
      encumbrance_status?: string;
      encumbrance_certificate_number?: string;
      mutation_status?: string;
      land_conversion_certificate?: {
        is_required?: boolean;
        status?: string;
        certificate_number?: string;
      };
      litigation_status?: string;
      legal_opinion_status?: string;
    };
    tax_and_utility?: {
      property_tax_receipts?: {
        receipt_number?: string;
        year?: string;
        status?: string;
      }[];
      electricity_connection?: {
        connection_number?: string;
        in_name_of?: string;
        status?: string;
      };
    };
    valuation_and_verification?: {
      market_value?: number;
      guideline_value?: number;
      technical_verification_status?: string;
      site_inspection_report_id?: string;
      photo_evidence?: string[];
    };
    miscellaneous?: {
      notarized?: boolean;
      scanned_copy_url?: string;
    };
     document_analysis_flags?: {
    "chain_of_ownership": [
  {"owner": "Mr. A", "transferred_to": "Ms. B", "date": "2005"},
  {"owner": "Ms. B", "transferred_to": "Mr. C", "date": "2012"},
  {"owner": "Mr. C", "transferred_to": "Mr. D", "date": "2020"}
]
    "cost_evaluation": {
      "consideration_price": number,               
      "guideline_value": number,                   
      "difference": "Above" | "Below" | "Equal",   
      "stamp_duty": {
        "paid": number,                           
        "expected": number,                        
        "rate": string                             
      },
      "remarks": string                           
    }

    "location_details": {
  "address": {
    "property_number": "",
    "street": "",
    "area": "",
    "village": "",
    "taluk": "",
    "district": "",
    "state": "",
    "pin_code": ""
  },
  "survey_info": {
    "survey_number": "",
    "plot_number": "",
    "door_number": ""
  },
  "boundary_description": {
    "north": "",
    "south": "",
    "east": "",
    "west": ""
  },
  "coordinates": {
    "latitude": null,
    "longitude": null,
    "source": "inferred" // or "document"
  },
  "consistency_check": {
    "status": "Consistent",
    "notes": ""
  }
}

    "signature_verification": {
  "status": "Mismatch Detected",
  "details": {
    "pages_with_signatures": [1, 4, 5],
    "signatures_mismatched": ["Page 4: Seller", "Page 5: Buyer"],
    "signed_on": "plain_white_paper",
    "notes": "Signature on page 4 is scanned. Buyer sign on page 5 doesn't match page 1."
  }
}

  };
};


"""

# custom_prompt = st.text_area("Prompt", default_prompt.strip(), height=150)

# custom_prompt = st.text_area("Prompt", default_prompt, height=150)

# Upload file
uploaded_file = st.file_uploader("Upload Document pdf", type=["pdf"])

def clean_json(text):
    if isinstance(text, dict):
        return text
    elif isinstance(text, str):
        cleaned = re.sub(r"```(?:json)?", "", text).strip("` \n")
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            st.error(f"⚠️ Failed to parse JSON: {e}")
            return {}
    else:
        st.error("⚠️ Invalid data type received.")
        return {}


def render_signature_verification(sig_data):
    st.markdown("### ✍️ Signature Verification")
    if isinstance(sig_data, dict):
        st.markdown(f"**Status:** {sig_data.get('status', 'NA')}")
        details = sig_data.get("details", {})
        if details:
            st.markdown(f"- 📝 **Signed On:** {details.get('signed_on', 'NA')}")
            st.markdown(f"- 📄 **Pages with Signatures:** {details.get('pages_with_signatures', [])}")
            st.markdown(f"- ❌ **Mismatches:** {', '.join(details.get('signatures_mismatched', [])) or 'None'}")
            st.markdown(f"- ⚠️ **Forgery Suspected:** {'Yes' if details.get('suspected_forgery') else 'No'}")
            st.markdown(f"- 📌 **Notes:** {details.get('notes', 'NA')}")
    else:
        st.write(sig_data or "No signature verification info found.")



GOOGLE_MAPS_API_KEY = ""


def get_lat_lon_from_address(address, api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception("Failed to connect to Google Maps API.")
    data = response.json()
    if data["status"] == "OK":
        result = data["results"][0]
        location = result["geometry"]["location"]
        return {
            "latitude": location["lat"],
            "longitude": location["lng"],
            "formatted_address": result["formatted_address"],
            "source": "google_geocoded"
        }
    else:
        raise Exception(f"Geocoding failed: {data.get('status')} - {data.get('error_message')}")

def render_location_details(loc):
    st.subheader("📍 Property Location Details")

    # 📌 Address
    st.markdown("### 📌 Address")
    address_fields = {
        "property_number": "Property No.",
        "street": "Street",
        "area": "Area",
        "village": "Village",
        "taluk": "Taluk",
        "district": "District",
        "state": "State",
        "pin_code": "PIN Code"
    }
    full_address = []
    for key, label in address_fields.items():
        value = loc.get("address", {}).get(key, "NA")
        st.write(f"**{label}:** {value}")
        full_address.append(value if value != "NA" else "")
    address_str = ", ".join(filter(None, full_address))

    # 🧾 Survey & Plot Info
    st.markdown("### 🧾 Survey & Plot Info")
    for key, label in {
        "survey_number": "Survey No.",
        "plot_number": "Plot No.",
        "door_number": "Door No."
    }.items():
        st.write(f"**{label}:** {loc.get('survey_info', {}).get(key, 'NA')}")

    # 🧭 Boundaries
    st.markdown("### 🧭 Boundaries")
    for side in ["north", "south", "east", "west"]:
        st.write(f"**{side.title()}:** {loc.get('boundary_description', {}).get(side, 'NA')}")

    # 🌐 Geo Coordinates
    st.markdown("### 🌐 Geo Coordinates")
    coords = loc.get("coordinates", {})
    lat = coords.get("latitude")
    lon = coords.get("longitude")
    formatted_address = coords.get("formatted_address", address_str)

    if not lat or not lon:
        try:
            geo = get_lat_lon_from_address(address_str, GOOGLE_MAPS_API_KEY)
            lat = geo["latitude"]
            lon = geo["longitude"]
            formatted_address = geo["formatted_address"]
            st.success("✅ Coordinates inferred using Google Maps API")
        except Exception as e:
            st.warning(f"⚠️ Latitude/Longitude not found or could not be inferred: {e}")
            lat, lon = None, None

    if lat and lon:
        st.write(f"**Latitude:** {lat}")
        st.write(f"**Longitude:** {lon}")
        st.write(f"**Source:** {coords.get('source', 'Google Maps')}")
        
        # ✅ Embed custom satellite map with marker + infowindow
        map_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            #map {{
              height: 450px;
              width: 100%;
            }}
          </style>
          <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}"></script>
          <script>
            function initMap() {{
              var location = {{ lat: {lat}, lng: {lon} }};
              var map = new google.maps.Map(document.getElementById('map'), {{
                zoom: 18,
                center: location,
                mapTypeId: 'satellite'
              }});
              var marker = new google.maps.Marker({{
                position: location,
                map: map,
                title: "Property Location"
              }});
              var infowindow = new google.maps.InfoWindow({{
                content: `<div style="font-size: 14px;">
                            <b>{formatted_address}</b><br>
                            📍 Lat: {lat}<br>
                            📍 Lon: {lon}
                          </div>`
              }});
              marker.addListener("click", () => {{
                infowindow.open(map, marker);
              }});
              infowindow.open(map, marker);
            }}
          </script>
        </head>
        <body onload="initMap()">
          <div id="map"></div>
        </body>
        </html>
        """
        components.html(map_html, height=500)

    # ✅ Consistency Check
    st.markdown("### ✅ Consistency Check")
    cc = loc.get("consistency_check", {})
    st.write(f"**Status:** {cc.get('status', 'NA')}")
    st.write(f"**Notes:** {cc.get('notes', 'NA')}")

def render_chain_of_ownership(chain_data):
    st.markdown("### 🔗 Chain of Ownership")

    def flow_block(owner_from, owner_to, date, is_first=False):
        return f"""
<div style="font-family:monospace; padding: 10px 0;">
    {'🔰' if is_first else '⬇️'} <b>{owner_from}</b><br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>
    <b>{owner_to}</b> <span style="color:gray;">(📅 {date})</span>
</div>
"""

    if isinstance(chain_data, list):
        for i, link in enumerate(chain_data):
            st.markdown(flow_block(
                link['owner'], link['transferred_to'], link.get('date', 'NA'), is_first=(i == 0)
            ), unsafe_allow_html=True)

    elif isinstance(chain_data, str):
        pattern = r"(?P<from>.*?)\s*→\s*(?P<to>.*?)(?:\s*\(Date:\s*(.*?)\))?"
        transitions = re.findall(pattern, chain_data)
        if transitions:
            for i, (from_owner, to_owner, date) in enumerate(transitions):
                st.markdown(flow_block(
                    from_owner.strip(), to_owner.strip(), date.strip() if date else 'NA', is_first=(i == 0)
                ), unsafe_allow_html=True)
        else:
            st.info("Could not parse chain format. Showing raw:")
            st.markdown(f"> {chain_data}")
    else:
        st.write("No structured ownership chain found.")
def render_cost_evaluation(cost_data):
    st.markdown("### 💰 Cost Evaluation")

    if isinstance(cost_data, dict):
        # Main price comparison
        consideration = cost_data.get('consideration_price', 'NA')
        guideline = cost_data.get('guideline_value', 'NA')
        difference = cost_data.get('difference', 'NA')

        st.markdown(f"""
- **Consideration Price:** ₹ {consideration:,}
- **Guideline Value:** ₹ {guideline:,}
- **Difference:** {'🔼 Above' if difference == 'Above' else '🔽 Below' if difference == 'Below' else '➖ Equal'}
""")

        # Stamp duty validation
        stamp = cost_data.get('stamp_duty', {})
        paid = stamp.get('paid', 'NA')
        expected = stamp.get('expected', 'NA')
        rate = stamp.get('rate', 'NA')

        st.markdown(f"""
- **Stamp Duty Paid:** ₹ {paid:,}
- **Expected Stamp Duty:** ₹ {expected:,}
- **Rate Applied:** {rate}
""")

        # Remarks
        st.markdown(f"📝 **Remarks:** {cost_data.get('remarks', 'NA')}")

    else:
        # Handle fallback string response
        st.markdown(f"💬 {cost_data or 'No cost evaluation info found.'}")

def render_property_deed_ui(data):
    print(data)
    deed = data.get("property_deed", {})
    st.title("📄 Property Deed Summary")
    flags = deed.get("document_analysis_flags", {})
    if flags:
        with st.expander("🚩 Document Analysis Flags", expanded=True):
            # Chain of Ownership
            chain_data = flags.get('chain_of_ownership')
            render_chain_of_ownership(chain_data)

            # Cost Evaluation
            render_cost_evaluation(flags.get("cost_evaluation"))

            # Location Details
            render_location_details(flags.get("location_details"))

            # Signature Verification
            sig_data = flags.get('signature_verification')
            render_signature_verification(sig_data)

            # # Signed Properly
            # st.markdown(f"### 📄 Signed Properly\n- {flags.get('signed_properly', 'NA')}")
    else:
        st.warning("⚠️ No document analysis flags found.")
    with st.expander("🆔 Document Info", expanded=True):
        col1, col2 = st.columns(2)
        col1.markdown(f"**📑 Document ID:** {deed.get('document_id', 'NA')}")
        col2.markdown(f"**📘 Deed Type:** {deed.get('deed_type', 'NA')}")

    with st.expander("📝 Registration Details", expanded=True):
        reg = deed.get("registration_details", {})
        st.markdown("""
        - 🔢 **Registration Number:** {}
        - 🗓️ **Registration Date:** {}
        - 🏢 **Sub-Registrar Office:** {}
        - 📍 **District:** {}
        """.format(
            reg.get('registration_number', 'NA'),
            reg.get('registration_date', 'NA'),
            reg.get('sub_registrar_office', 'NA'),
            reg.get('registration_district', 'NA')
        ))

    with st.expander("👥 Parties Involved", expanded=True):
        parties = deed.get("parties", {})
        seller = parties.get("seller", {})
        buyer = parties.get("buyer", {})
        poa = parties.get("power_of_attorney", {})

        st.markdown("### 🔴 Seller")
        st.markdown(f"""
        - **Name:** {seller.get('name', 'NA')}
        - **Address:** {seller.get('address', 'NA')}
        - **PAN:** {seller.get('pan', 'NA')}
        - **Aadhaar:** {seller.get('aadhaar', 'NA')}
        """)

        st.markdown("### 🟢 Buyer")
        st.markdown(f"""
        - **Name:** {buyer.get('name', 'NA')}
        - **Address:** {buyer.get('address', 'NA')}
        - **PAN:** {buyer.get('pan', 'NA')}
        - **Aadhaar:** {buyer.get('aadhaar', 'NA')}
        """)

        st.markdown("### 📝 Power of Attorney")
        st.markdown(f"""
        - **Applicable:** {poa.get('is_applicable', 'NA')}
        - **Details:** {poa.get('details', 'NA')}
        """)

    with st.expander("📍 Property Details", expanded=True):
        prop = deed.get("property_details", {})
        extent = prop.get("extent", {})
        boundary = prop.get("boundary_description", {})

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            - **Survey Number:** {prop.get('survey_number', 'NA')}
            - **Plot Number:** {prop.get('plot_number', 'NA')}
            - **Door Number:** {prop.get('door_number', 'NA')}
            - **Land Area (sqft):** {extent.get('land_area_sqft', 'NA')}
            """)
        with col2:
            st.markdown(f"""
            - **Built-up Area (sqft):** {extent.get('builtup_area_sqft', 'NA')}
            - **Village:** {prop.get('village', 'NA')}
            - **Taluk:** {prop.get('taluk', 'NA')}
            - **District:** {prop.get('district', 'NA')}
            """)

        st.markdown(f"""
        - **State:** {prop.get('state', 'NA')}
        - **PIN Code:** {prop.get('pin_code', 'NA')}
        - **Address:** {prop.get('property_address', 'NA')}
        """)

        st.markdown("**🧭 Boundaries**")
        st.markdown(f"""
        - 🧭 North: {boundary.get('north', 'NA')}
        - 🧭 South: {boundary.get('south', 'NA')}
        - 🧭 East: {boundary.get('east', 'NA')}
        - 🧭 West: {boundary.get('west', 'NA')}
        """)

    with st.expander("⚖️ Legal Info", expanded=True):
        legal = deed.get("legal_info", {})
        land_conv = legal.get("land_conversion_certificate", {})

        st.markdown(f"""
        - **Ownership Type:** {legal.get('ownership_type', 'NA')}
        - **Land Use:** {legal.get('land_use_type', 'NA')}
        - **Encumbrance Status:** {legal.get('encumbrance_status', 'NA')}
        - **Mutation Status:** {legal.get('mutation_status', 'NA')}
        - **Litigation Status:** {legal.get('litigation_status', 'NA')}
        """)

        st.markdown("**📜 Land Conversion Certificate**")
        st.markdown(f"""
        - **Required:** {land_conv.get('is_required', 'NA')}
        - **Status:** {land_conv.get('status', 'NA')}
        - **Certificate Number:** {land_conv.get('certificate_number', 'NA')}
        """)

    with st.expander("💡 Tax & Utilities", expanded=True):
        tax = deed.get("tax_and_utility", {})
        receipts = tax.get("property_tax_receipts", [])
        elec = tax.get("electricity_connection", {})

        st.markdown("**💸 Property Tax Receipts**")
        if receipts:
            for i, r in enumerate(receipts):
                st.markdown(f"- 🔖 **[{i+1}]** Receipt No: {r.get('receipt_number', 'NA')}, Year: {r.get('year', 'NA')}, Status: {r.get('status', 'NA')}")
        else:
            st.write("No receipts available.")

        st.markdown("**🔌 Electricity Connection**")
        st.markdown(f"""
        - **Connection Number:** {elec.get('connection_number', 'NA')}
        - **In Name of:** {elec.get('in_name_of', 'NA')}
        - **Status:** {elec.get('status', 'NA')}
        """)

    with st.expander("💰 Valuation & Verification", expanded=True):
        val = deed.get("valuation_and_verification", {})
        st.markdown(f"""
        - 💸 **Market Value:** ₹ {val.get('market_value', 'NA')}
        - 📏 **Guideline Value:** {val.get('guideline_value', 'NA')}
        - ✅ **Technical Verification:** {val.get('technical_verification_status', 'NA')}
        - 🧾 **Site Inspection ID:** {val.get('site_inspection_report_id', 'NA')}
        """)

    with st.expander("🧾 Miscellaneous", expanded=True):
        misc = deed.get("miscellaneous", {})
        st.markdown(f"""
        - **Notarized:** {misc.get('notarized', 'NA')}
        - **Scanned Copy:** [Link]({misc.get('scanned_copy_url', '#')})
        """ if misc.get('scanned_copy_url') else "- Scanned copy not available.")

# Final JSON show + UI render
def show_output(text):
    parsed = clean_json(text)
    if isinstance(parsed, dict):
        render_property_deed_ui(parsed)
    else:
        st.subheader("📦 Output (Raw Text)")
        st.code(text)
        st.error("⚠️ Output is not valid JSON.")

# Process uploaded file
if uploaded_file:
    file_bytes = uploaded_file.read()
    mime_type, _ = guess_type(uploaded_file.name)

    if mime_type and mime_type.startswith("image/"):
        try:
            img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            st.image(img, caption="Uploaded Image", use_column_width=True)
            st.write("⏳ Processing ...")
            response = model.generate_content([default_prompt.strip(), img])
            show_output(response.text)
        except Exception as e:
            st.error(f"Error reading image: {e}")

    elif mime_type == "application/pdf":
        encoded_pdf = base64.b64encode(file_bytes).decode("utf-8")
        file_part = {
            "mime_type": mime_type,
            "data": encoded_pdf
        }
        st.write("⏳ Processing DOCUMENT...")
        response = model.generate_content([default_prompt.strip(), file_part])
        show_output(response.text)

    else:
        st.error("Unsupported file type. Please upload a JPG, PNG, or PDF.")
