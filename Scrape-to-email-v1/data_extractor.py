def extract_fields(studies):
    """Extract relevant fields from study data"""
    extracted_data = []
    
    for study in studies:
        protocol = study.get('protocolSection', {})
        
        study_data = {
            # Key identifiers
            'nct_id': protocol.get('identificationModule', {}).get('nctId'),
            'brief_title': protocol.get('identificationModule', {}).get('briefTitle'),
            'official_title': protocol.get('identificationModule', {}).get('officialTitle'),
            
            # Status info
            'status': protocol.get('statusModule', {}).get('overallStatus'),
            'phase': protocol.get('designModule', {}).get('phases', []),
            'study_type': protocol.get('designModule', {}).get('studyType'),
            
            # Dates
            'start_date': protocol.get('statusModule', {}).get('startDateStruct', {}).get('date'),
            'completion_date': protocol.get('statusModule', {}).get('completionDateStruct', {}).get('date'),
            
            # Study details
            'conditions': protocol.get('conditionsModule', {}).get('conditions', []),
            'enrollment': protocol.get('designModule', {}).get('enrollmentInfo', {}).get('count'),
            'eligibility_criteria': protocol.get('eligibilityModule', {}).get('eligibilityCriteria'),
            
            # Outcomes 
            'primary_outcomes': protocol.get('outcomesModule', {}).get('primaryOutcomes', []),
            'secondary_outcomes': protocol.get('outcomesModule', {}).get('secondaryOutcomes', []),
            
            # Contact info
            'sponsor': protocol.get('sponsorCollaboratorsModule', {}).get('leadSponsor', {}).get('name'),
            'central_contacts': protocol.get('contactsLocationsModule', {}).get('centralContacts', []),
            'locations': protocol.get('contactsLocationsModule', {}).get('locations', [])
        }
        
        extracted_data.append(study_data)
            
    return extracted_data