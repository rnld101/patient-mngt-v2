/**
 * Error handler utility to extract meaningful error messages from API responses.
 * Handles both FastAPI validation errors and HTTP exceptions.
 */

/**
 * Extract a user-friendly error message from an Axios error.
 * Handles FastAPI validation errors (array detail), HTTP exceptions
 * (string detail), network errors, and unknown errors.
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

  // FastAPI validation errors arrive as an array of error objects
  if (Array.isArray(data?.detail)) {
    return extractValidationErrors(data.detail)
  }

  // HTTP exceptions arrive as a plain string
  if (typeof data?.detail === 'string') {
    return data.detail
  }

  return data?.message || 'An error occurred'
}

/**
 * Format FastAPI validation errors into a readable multi-line string.
 */
const extractValidationErrors = (errors) => {
  if (!Array.isArray(errors) || errors.length === 0) {
    return 'Validation failed'
  }

  const messages = errors.map(error => {
    if (error.msg) return error.msg
    if (error.type) return formatErrorType(error.type, error.loc)
    return 'Validation error'
  })

  return messages.join('\n')
}

/**
 * Map a FastAPI error type to a human-readable message.
 */
const formatErrorType = (type, loc) => {
  const fieldName = loc?.[loc.length - 1] || 'field'

  const errorMessages = {
    'string_too_short': `${fieldName} is too short`,
    'string_too_long': `${fieldName} is too long`,
    'value_error': `Invalid value for ${fieldName}`,
    'type_error': `Invalid type for ${fieldName}`,
    'value_error.email': 'Please enter a valid email',
    'value_error.number.not_ge': `${fieldName} must be greater than 0`,
    'value_error.number.not_le': `${fieldName} is too large`,
  }

  return errorMessages[type] || `Validation error for ${fieldName}`
}
