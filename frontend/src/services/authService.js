import api from './api'

export const authService = {
  register: (username, email, password) => {
    return api.post('/auth/register', { username, email, password })
  },

  login: (email, password) => {
    return api.post('/auth/login', { email, password })
  },
}
