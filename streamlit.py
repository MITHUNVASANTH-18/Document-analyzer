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


load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# model = genai.GenerativeModel("gemini-1.5-flash")

st.title("📄 Document Analyzer")


model = genai.GenerativeModel("gemini-2.5-pro-preview-05-06")


default_prompt = """
Analyze the given document. First, detect the source language of the document. If it is not in English, then translate it into English before proceeding.

Then, deeply analyze the content — ultra-deep, ultra-important, ultra-analyze — and extract the useful features in the given format. If you can't find any value for a field, just put "NA" or "not assigned", but make the output as reliable as possible. Reliability is a key factor here — very important.

⚠️ Strictly return the output ONLY as a raw JSON object that matches the following schema. Do not wrap it in markdown or provide any extra explanation.

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
  };
};


"""

# custom_prompt = st.text_area("Prompt", default_prompt.strip(), height=150)

# custom_prompt = st.text_area("Prompt", default_prompt, height=150)

# Upload file
uploaded_file = st.file_uploader("Upload Document pdf", type=["pdf"])

def clean_json(text):
    # Strip markdown-like wrappers
    cleaned = re.sub(r"```(?:json)?", "", text).strip("` \n")
    return cleaned
# Helper to render structured UI
def render_property_deed_ui(data):
    deed = data.get("property_deed", {})

    st.subheader("📄 Property Deed Summary")

    with st.expander("🆔 Document Info", expanded=True):
        st.write(f"**Document ID:** {deed.get('document_id', 'NA')}")
        st.write(f"**Deed Type:** {deed.get('deed_type', 'NA')}")

    with st.expander("📝 Registration Details", expanded=True):
        reg = deed.get("registration_details", {})
        st.write(f"**Registration Number:** {reg.get('registration_number', 'NA')}")
        st.write(f"**Registration Date:** {reg.get('registration_date', 'NA')}")
        st.write(f"**Sub-Registrar Office:** {reg.get('sub_registrar_office', 'NA')}")
        st.write(f"**District:** {reg.get('registration_district', 'NA')}")

    with st.expander("👥 Parties Involved", expanded=True):
        parties = deed.get("parties", {})
        seller = parties.get("seller", {})
        buyer = parties.get("buyer", {})
        poa = parties.get("power_of_attorney", {})

        st.markdown("**🔴 Seller:**")
        st.write(f"- Name: {seller.get('name', 'NA')}")
        st.write(f"- Address: {seller.get('address', 'NA')}")
        st.write(f"- PAN: {seller.get('pan', 'NA')}")
        st.write(f"- Aadhaar: {seller.get('aadhaar', 'NA')}")

        st.markdown("**🟢 Buyer:**")
        st.write(f"- Name: {buyer.get('name', 'NA')}")
        st.write(f"- Address: {buyer.get('address', 'NA')}")
        st.write(f"- PAN: {buyer.get('pan', 'NA')}")
        st.write(f"- Aadhaar: {buyer.get('aadhaar', 'NA')}")

        st.markdown("**📝 Power of Attorney:**")
        is_applicable = poa.get("is_applicable", True)
        st.write(f"- Applicable: {is_applicable}")
        st.write(f"- Details: {poa.get('details', 'NA')}")

    with st.expander("📍 Property Details", expanded=True):
        prop = deed.get("property_details", {})
        extent = prop.get("extent", {})
        boundary = prop.get("boundary_description", {})

        st.write(f"**Survey Number:** {prop.get('survey_number', 'NA')}")
        st.write(f"**Plot Number:** {prop.get('plot_number', 'NA')}")
        st.write(f"**Door Number:** {prop.get('door_number', 'NA')}")
        st.write(f"**Land Area (sqft):** {extent.get('land_area_sqft', 'NA')}")
        st.write(f"**Built-up Area (sqft):** {extent.get('builtup_area_sqft', 'NA')}")
        st.write(f"**Address:** {prop.get('property_address', 'NA')}")
        st.write(f"**Village:** {prop.get('village', 'NA')}")
        st.write(f"**Taluk:** {prop.get('taluk', 'NA')}")
        st.write(f"**District:** {prop.get('district', 'NA')}")
        st.write(f"**State:** {prop.get('state', 'NA')}")
        st.write(f"**PIN Code:** {prop.get('pin_code', 'NA')}")

        st.markdown("**🧭 Boundaries:**")
        st.write(f"- North: {boundary.get('north', 'NA')}")
        st.write(f"- South: {boundary.get('south', 'NA')}")
        st.write(f"- East: {boundary.get('east', 'NA')}")
        st.write(f"- West: {boundary.get('west', 'NA')}")

    with st.expander("⚖️ Legal Info", expanded=True):
        legal = deed.get("legal_info", {})
        land_conv = legal.get("land_conversion_certificate", {})

        st.write(f"**Ownership Type:** {legal.get('ownership_type', 'NA')}")
        st.write(f"**Land Use:** {legal.get('land_use_type', 'NA')}")
        st.write(f"**Encumbrance Status:** {legal.get('encumbrance_status', 'NA')}")
        st.write(f"**Mutation Status:** {legal.get('mutation_status', 'NA')}")
        st.write(f"**Litigation Status:** {legal.get('litigation_status', 'NA')}")
        st.write(f"**Legal Opinion Status:** {legal.get('legal_opinion_status', 'NA')}")

        st.markdown("**📜 Land Conversion Certificate:**")
        st.write(f"- Required: {land_conv.get('is_required', 'NA')}")
        st.write(f"- Status: {land_conv.get('status', 'NA')}")
        st.write(f"- Certificate No: {land_conv.get('certificate_number', 'NA')}")

    with st.expander("💡 Tax & Utilities", expanded=True):
        tax = deed.get("tax_and_utility", {})
        receipts = tax.get("property_tax_receipts", [])
        elec = tax.get("electricity_connection", {})

        st.markdown("**💸 Property Tax Receipts:**")
        for i, r in enumerate(receipts):
            st.write(f"• [{i+1}] Receipt No: {r.get('receipt_number', 'NA')}, Year: {r.get('year', 'NA')}, Status: {r.get('status', 'NA')}")

        st.markdown("**🔌 Electricity Connection:**")
        st.write(f"- Connection No: {elec.get('connection_number', 'NA')}")
        st.write(f"- In Name of: {elec.get('in_name_of', 'NA')}")
        st.write(f"- Status: {elec.get('status', 'NA')}")

    with st.expander("💰 Valuation & Verification", expanded=True):
        val = deed.get("valuation_and_verification", {})
        st.write(f"**Market Value:** ₹ {val.get('market_value', 'NA')}")
        st.write(f"**Guideline Value:** {val.get('guideline_value', 'NA')}")
        st.write(f"**Technical Verification:** {val.get('technical_verification_status', 'NA')}")
        st.write(f"**Site Inspection ID:** {val.get('site_inspection_report_id', 'NA')}")

    with st.expander("🧾 Miscellaneous", expanded=True):
        misc = deed.get("miscellaneous", {})
        st.write(f"**Notarized:** {misc.get('notarized', 'NA')}")
        st.write(f"**Scanned Copy URL:** {misc.get('scanned_copy_url', 'NA')}")


# Final JSON show + UI render
def show_output(text):
    cleaned = clean_json(text)
    try:
        parsed = json.loads(cleaned)
        # st.subheader("📦 Extracted JSON")
        # st.json(parsed)

        # Custom structured UI
        render_property_deed_ui(parsed)

    except Exception as e:
        st.subheader("📦 Output (Raw Text)")
        st.code(text)
        st.error(f"⚠️ Output is not valid JSON: {e}")

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
