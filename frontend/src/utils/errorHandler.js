/**
 * Error handler utility to extract meaningful error messages from API responses
 * Handles both FastAPI validation errors and HTTP exceptions
 */

/**
 * Extract error message from API error response
 * 
 * Handles:
 * - FastAPI validation errors (array of error objects)
 * - HTTP exceptions (string detail)
 * - Network errors
 * - Unknown errors
 * 
 * @param {Error} err - The error object from axios
 * @returns {string} - User-friendly error message
 */
export const getErrorMessage = (err) => {
  // Network error or no response
  if (!err.response) {
    if (err.message === 'Network Error') {
      return 'Network error. Please check your internet connection.'
    }
    return err.message || 'An unexpected error occurred'
  }

  const { data } = err.response

  // Handle FastAPI validation errors (array format)
  if (Array.isArray(data?.detail)) {
    return extractValidationErrors(data.detail)
  }

  // Handle HTTP exceptions (string format)
  if (typeof data?.detail === 'string') {
    return data.detail
  }

  // Fallback to generic error message
  return data?.message || 'An error occurred'
}

/**
 * Extract and format validation errors from FastAPI response
 * 
 * @param {Array} errors - Array of FastAPI validation error objects
 * @returns {string} - Formatted error message
 */
const extractValidationErrors = (errors) => {
  if (!Array.isArray(errors) || errors.length === 0) {
    return 'Validation failed'
  }

  // Extract messages from validation errors
  const messages = errors.map(error => {
    if (error.msg) {
      return error.msg
    }
    if (error.type) {
      return formatErrorType(error.type, error.loc)
    }
    return 'Validation error'
  })

  // Join messages with line breaks for readability
  return messages.join('\n')
}

/**
 * Format FastAPI error type to human-readable message
 * 
 * @param {string} type - Error type from FastAPI
 * @param {Array} loc - Field location
 * @returns {string} - Formatted error message
 */
const formatErrorType = (type, loc) => {
  const fieldName = loc?.[loc.length - 1] || 'field'

  const errorMessages = {
    'string_too_short': `${fieldName} is too short`,
    'string_too_long': `${fieldName} is too long`,
    'value_error': `Invalid value for ${fieldName}`,
    'type_error': `Invalid type for ${fieldName}`,
    'value_error.email': `Please enter a valid email`,
    'value_error.number.not_ge': `${fieldName} must be greater than 0`,
    'value_error.number.not_le': `${fieldName} is too large`,
  }

  return errorMessages[type] || `Validation error for ${fieldName}`
}

/**
 * Check if error is a validation error
 * 
 * @param {Error} err - Error object from axios
 * @returns {boolean} - True if validation error
 */
export const isValidationError = (err) => {
  return Array.isArray(err?.response?.data?.detail)
}

/**
 * Check if error is an authentication error
 * 
 * @param {Error} err - Error object from axios
 * @returns {boolean} - True if 401 unauthorized
 */
export const isAuthError = (err) => {
  return err?.response?.status === 401
}

/**
 * Check if error is a conflict error (e.g., duplicate user)
 * 
 * @param {Error} err - Error object from axios
 * @returns {boolean} - True if 409 conflict
 */
export const isConflictError = (err) => {
  return err?.response?.status === 409
}

/**
 * Check if error is a server error
 * 
 * @param {Error} err - Error object from axios
 * @returns {boolean} - True if 5xx error
 */
export const isServerError = (err) => {
  return err?.response?.status >= 500
}
